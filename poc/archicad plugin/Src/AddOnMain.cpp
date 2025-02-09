#include "APIEnvir.h"
#include "ACAPinc.h"
#include <codecvt>
#include <locale>

#include "ResourceIds.hpp"
#include "DGModule.hpp"
#include "APIdefs_Attributes.h"

#include <fstream>
#include <iostream>
#include <sstream>
#include <ctime>
#include <thread>

#include <boost/asio/io_context.hpp>
#include <boost/asio/detached.hpp>
#include <boost/asio/ip/tcp.hpp>
#include <boost/json.hpp>
#include <boost/json/src.hpp>

#include <boost/asio/use_awaitable.hpp>
#include <boost/asio/as_tuple.hpp>
#include <boost/asio/co_spawn.hpp>
#include <boost/asio/deferred.hpp>
#include <boost/asio/detached.hpp>
#include <boost/asio/io_context.hpp>
#include <boost/asio/signal_set.hpp>
#include <boost/asio/ip/tcp.hpp>

#include <async_mqtt5/mqtt_client.hpp>
#include <async_mqtt5/types.hpp>
#include <async_mqtt5/reason_codes.hpp>
#include <async_mqtt5/logger.hpp>

#include <../Modules/GSRoot/MessageLoopExecutor.hpp>


namespace json = boost::json;

// Global Variables
std::unique_ptr<std::thread> mqttThread;
boost::asio::io_context ioc;
async_mqtt5::mqtt_client<boost::asio::ip::tcp::socket> client(ioc);
std::atomic<bool> running(true);

std::ofstream logfile;

void PublishMessage() {
    
    // Open the selected file for writing
    std::ostringstream messageStream;
    
    GSErrCode err;
    GS::Array<API_Attribute> compositeAttributes;
    
    // Step 1: Retrieve all composite attributes
    err = ACAPI_Attribute_GetAttributesByType(API_CompWallID, compositeAttributes);
    if (err != NoError) {
        messageStream << "Error retrieving composites: " << err << std::endl;
        return;
    }

    // Step 2: Print the number of composites
    //messageStream << "Number of composites: " << compositeAttributes.GetSize() << std::endl;
    
    messageStream << R"(
      {
          "operation_type": "update",
          "author": "Roman Rust",
          "timestamp": ")" << std::time(nullptr) << R"(",
          "globalId": "8d0fbb28-fe53-488a-a92b-a5a3c1af7a75",
          "data": 
              [
    )";

    // Step 3: Iterate through composites
    for (UInt32 i = 0; i < compositeAttributes.GetSize(); ++i) {
        API_Attribute& composite = compositeAttributes[i];
        //messageStream << "Composite " << (i + 1) << ": " << composite.header.name << std::endl;
        std::string compositename = composite.header.name;
        
        if(compositename != "WBW_Aussenwand_Beton 54") continue;
        
        messageStream << R"(
                {
                  "type": "IfcMaterialLayerSet",
                  "layerSetName":  ")" << compositename << R"(" ,
                  "materialLayers": [ )";
        
        // Step 4: Retrieve composite definition to access layers
        API_AttributeDefExt    compositeDef;
        BNZeroMemory(&compositeDef, sizeof(API_AttributeDefExt));

        err = ACAPI_Attribute_GetDefExt (composite.header.typeID, composite.header.index, &compositeDef);
        if (err != NoError) {
            messageStream << "  Error retrieving layers for composite: " << composite.header.name << " (" << err << ")" << std::endl;
            continue;
        }
        
        if (compositeDef.cwall_compItems != nullptr) {
            Int32 layerCount = BMGetHandleSize(reinterpret_cast<GSHandle>(compositeDef.cwall_compItems)) / sizeof(API_CWallComponent);
            for (Int32 i = 0; i < layerCount; ++i) {
                API_CWallComponent layer = (*compositeDef.cwall_compItems)[i];
                //messageStream << "  Layer " << (i + 1) << ": Thickness = " << layer.fillThick << std::endl;
                
                //layer.fillThick = 0.0;
                //ACAPI_Attribute_ModifyExt(&composite, &compositeDef);
                
                // Fetch material info
                API_Attribute material;
                BNZeroMemory(&material, sizeof(API_Attribute));
                material.header.typeID = API_BuildingMaterialID;  // Material attribute type
                material.header.index = layer.buildingMaterial;
                err = ACAPI_Attribute_Get(&material);
                if(err == NoError) {
                    GS::UniString materialName(material.header.name);
                    
                    if(err == NoError) {
                        //messageStream << "    Material " << materialName << ": Density = " << material.buildingMaterial.density << std::endl;
                        
                        messageStream << R"(
                        {
                            "type": "IfcMaterialLayer",
                            "material": {
                                "type": "IfcMaterial",
                                "name": ")" + materialName + R"("
                            },
                            "layerThickness": ")" + std::to_string(layer.fillThick) + R"(",
                            "isVentilated": false,
                            "name": ")" + materialName + R"("
                        }, 
                        )";
                        
                        //ACAPI_DisposeAttrDefsHdlsExt(&materialProperty);
                    }
                    else {
                        messageStream << "    Material " << materialName << ": x = (error) " << std::endl;
                    }
                }
                else {
                    messageStream << "    Failed to fetch material for layer. Error code: " << err;
                }
            }
            
            break; // only first component!
        }
        
        messageStream << R"(
                ]
        )";
        
        messageStream << R"(
            },
        )";
        
        // Free memory allocated for the composite definition
        ACAPI_DisposeAttrDefsHdlsExt(&compositeDef);
    }

    messageStream << R"(
            ]}
    )";

    try {
    
        //boost::asio::io_context ioc;
        //async_mqtt5::mqtt_client<boost::asio::ip::tcp::socket> c(ioc);

        //c.brokers("85.215.121.128", 1883)
        //    .credentials("archicad", "", "")
        //    .async_run(boost::asio::detached);

        std::string message = messageStream.str();
        
        
        client.async_publish<async_mqtt5::qos_e::at_most_once>(
            "ifc/test", message,
            async_mqtt5::retain_e::no, async_mqtt5::publish_props {},
            [&messageStream](async_mqtt5::error_code ec) {
                  if (ec) {
                      messageStream << "MQTT Publish Error: " << ec.message() << std::endl;
                  } else {
                      messageStream << "Message published successfully!" << std::endl;
                  }
                  //client.async_disconnect(boost::asio::detached); // Disconnect after publishing
              }
        );
        
        //ioc.run();
        
        sleep(3);
        
        messageStream << "Sent! v17";
     
    } catch (const std::exception& e) {
        messageStream << "Exception caught: " << e.what() << std::endl;
    } catch (...) {
        messageStream << "Unknown exception caught!" << std::endl;
    }
    
    std::ofstream outFile("/Users/adrianhenke/composite_data.txt");
    if (outFile.is_open()) {
        outFile << messageStream.str();
        outFile.close();
        ACAPI_WriteReport("Component successfully published to IFC DATA BUS.", true);
    } else {
        ACAPI_WriteReport("Failed to write to file.", true);
    }
}




static const GSResID AddOnInfoID            = ID_ADDON_INFO;
    static const Int32 AddOnNameID            = 1;
    static const Int32 AddOnDescriptionID    = 2;

static const short AddOnMenuID                = ID_ADDON_MENU;
    static const Int32 AddOnCommandID        = 1;

class ExampleDialog :    public DG::ModalDialog,
                        public DG::PanelObserver,
                        public DG::ButtonItemObserver,
                        public DG::CompoundItemObserver
{
public:
    enum DialogResourceIds
    {
        ExampleDialogResourceId = ID_ADDON_DLG,
        OKButtonId = 1,
        CancelButtonId = 2,
        SeparatorId = 3
    };

    ExampleDialog () :
        DG::ModalDialog (ACAPI_GetOwnResModule (), ExampleDialogResourceId, ACAPI_GetOwnResModule ()),
        okButton (GetReference (), OKButtonId),
        cancelButton (GetReference (), CancelButtonId),
        separator (GetReference (), SeparatorId)
    {
        AttachToAllItems (*this);
        Attach (*this);
    }

    ~ExampleDialog ()
    {
        Detach (*this);
        DetachFromAllItems (*this);
    }

private:
    virtual void PanelResized (const DG::PanelResizeEvent& ev) override
    {
        BeginMoveResizeItems ();
        okButton.Move (ev.GetHorizontalChange (), ev.GetVerticalChange ());
        cancelButton.Move (ev.GetHorizontalChange (), ev.GetVerticalChange ());
        separator.MoveAndResize (0, ev.GetVerticalChange (), ev.GetHorizontalChange (), 0);
        EndMoveResizeItems ();
    }

    virtual void ButtonClicked (const DG::ButtonClickEvent& ev) override
    {
        if (ev.GetSource () == &okButton) {

            PublishMessage();

            //PostCloseRequest (DG::ModalDialog::Accept);
            
        } else if (ev.GetSource () == &cancelButton) {
            PostCloseRequest (DG::ModalDialog::Cancel);
        }
    }

    DG::Button        okButton;
    DG::Button        cancelButton;
    DG::Separator    separator;
};

static GSErrCode MenuCommandHandler (const API_MenuParams *menuParams)
{
    switch (menuParams->menuItemRef.menuResID) {
        case AddOnMenuID:
            switch (menuParams->menuItemRef.itemIndex) {
                case AddOnCommandID:
                    {
                        ExampleDialog dialog;
                        dialog.Invoke ();
                    }
                    break;
            }
            break;
    }
    return NoError;
}

API_AddonType CheckEnvironment (API_EnvirParams* envir)
{
    RSGetIndString (&envir->addOnInfo.name, AddOnInfoID, AddOnNameID, ACAPI_GetOwnResModule ());
    RSGetIndString (&envir->addOnInfo.description, AddOnInfoID, AddOnDescriptionID, ACAPI_GetOwnResModule ());

    return APIAddon_Normal;
}

GSErrCode RegisterInterface (void)
{
#ifdef ServerMainVers_2700
    return ACAPI_MenuItem_RegisterMenu (AddOnMenuID, 0, MenuCode_Tools, MenuFlag_Default);
#else
    return ACAPI_Register_Menu (AddOnMenuID, 0, MenuCode_Tools, MenuFlag_Default);
#endif
}



#include <iostream>
#include <fstream>
#include <boost/json.hpp>
#include "APIEnvir.h"
#include "ACAPinc.h"

// Function to parse JSON file
boost::json::value parseJsonFile(const std::string& filename) {
    std::ifstream file(filename);
    if (!file) {
        throw std::runtime_error("Error opening JSON file: " + filename);
    }

    std::stringstream buffer;
    buffer << file.rdbuf();
    file.close();

    return boost::json::parse(buffer.str());
}

// Function to update composite attributes (runs on UI thread)
GSErrCode UpdateCompositeFromJson(const boost::json::value& json) {
    logfile << "Running update on UI thread .." << std::endl;

    const auto& data = json.at("data").at("data").as_array();
    
    logfile << json.at("operation_type").as_string().c_str() << std::endl;
    logfile << data.size() << std::endl;

    for (const auto& layerSet : data) {
        std::string compositeName = layerSet.at("layerSetName").as_string().c_str();
        logfile << "Processing Composite: " << GS::UniString(compositeName.c_str()) << std::endl;
        logfile.flush();

        // Fetch composite by name
        GS::Array<API_Attribute> compositeAttributes;
        GSErrCode err = ACAPI_Attribute_GetAttributesByType(API_CompWallID, compositeAttributes);
        if (err != NoError) {
            logfile << "Error retrieving composites" << std::endl;
            return err;
        }

        Boolean found = false;
        for (auto& composite : compositeAttributes) {
            if (GS::UniString(composite.header.name) == compositeName) {
                logfile << "Found composite: " << compositeName << std::endl;
                found = true;
                
                API_AttributeDefExt compositeDef;
                BNZeroMemory(&compositeDef, sizeof(API_AttributeDefExt));

                err = ACAPI_Attribute_GetDefExt(composite.header.typeID, composite.header.index, &compositeDef);
                if (err != NoError) {
                    logfile << "Failed to fetch composite definition." << std::endl;
                    continue;
                }
                logfile << "Fetched composite" << std::endl;

                bool needsUpdate = false;

                // Iterate through layers and update
                if (compositeDef.cwall_compItems != nullptr) {
                    Int32 layerCount = BMGetHandleSize(reinterpret_cast<GSHandle>(compositeDef.cwall_compItems)) / sizeof(API_CWallComponent);
                    const auto& layers = layerSet.at("materialLayers").as_array();

                    for (Int32 i = 0; i < layerCount && i < layers.size(); ++i) {
                        logfile << "Processing layer no " << i << std::endl;
                        
                        API_CWallComponent layer = (*compositeDef.cwall_compItems)[i];
                        const auto& jsonLayer = layers[i];

                        // Update layer thickness
                        layer.fillThick = jsonLayer.at("layerThickness").as_double();
                        logfile << GS::UniString("Updated Layer Thickness: ") << GS::UniString(std::to_string(layer.fillThick).c_str()) << " mm" << std::endl;
                        needsUpdate = true;
                        
                        break;

                        // Update material density if material exists
                        /*
                        if (jsonLayer.as_object().contains("material")) {
                            API_Attribute material;
                            BNZeroMemory(&material, sizeof(API_Attribute));
                            material.header.typeID = API_BuildingMaterialID;
                            material.header.index = layer.buildingMaterial;

                            err = ACAPI_Attribute_Get(&material);
                            if (err == NoError) {
                                material.buildingMaterial.density = 2000.0; // Example density update
                                err = ACAPI_Attribute_ModifyExt(&material, nullptr);
                                if (err == NoError) {
                                    logfile << "  Material Density Updated: 2000 kg/m³";
                                }
                                needsUpdate = true;
                            }
                        }*/
                    }
                }

                // Save updated composite only if changes were made
                if (needsUpdate) {
                    err = ACAPI_Attribute_ModifyExt(&composite, &compositeDef);
                    
                    if (err == NoError) {
                        logfile << "Composite Updated Successfully!";
                    }
                }

                // Free memory
                ACAPI_DisposeAttrDefsHdlsExt(&compositeDef);
            }
        }
        if(!found) logfile << "Composite not found: " << compositeName;
    }
    return NoError;
}

class FunctionRunnable : public GS::Runnable {
public:
    // Constructor takes a std::function to execute.
    FunctionRunnable (std::function<void()> func)
        : f(std::move(func))
    { }

    // Override the pure virtual method Run().
    virtual void Run() override {
        f();
    }
    
private:
    std::function<void()> f;
};

// Function to safely call updates from another thread
void ScheduleCompositeUpdate(const boost::json::value& parsed_json) {
    logfile << "Scheduling composite update..." << std::endl;
    logfile.flush();
    
    GS::RunnableTask task(new FunctionRunnable([&]() {
        UpdateCompositeFromJson(parsed_json);
    }));

    GS::MessageLoopExecutor executor;
    executor.Execute(task, GS::Message::Normal);


    logfile << "Composite update scheduled!";
}

boost::json::value parsed_json;

void receive_loop(async_mqtt5::mqtt_client<boost::asio::ip::tcp::socket>& client) {
    logfile << "Waiting for messages..." << std::endl;
    
    client.async_receive(
        boost::asio::bind_executor(
            client.get_executor(),
            [&client](async_mqtt5::error_code ec, std::string topic, std::string payload, async_mqtt5::publish_props publish_props) {
                if (ec) {
                    logfile << "Receive Error: " << ec.message() << std::endl;
                    return; // Stop if there is an error
                }

                // Log the received message
                logfile << "Received message on topic: " << topic << std::endl;
                logfile << "Message: " << payload << std::endl;
                
                try {
                    parsed_json = boost::json::parse(payload);
                    logfile << "parsed payload" << std::endl;
                    
                    ScheduleCompositeUpdate(parsed_json);
                }
                catch (const std::exception& e) {
                    logfile << GS::UniString(e.what());
                    logfile.flush();
                }
                    
                receive_loop(client);
            }
        )
    );
}
    

// Function to Run MQTT Client
void StartMqttClient() {
    try {

        logfile << "v20" << std::endl;
        logfile << "setting up mqtt client" << std::endl;
        
        //boost::asio::io_context ioc;
        //async_mqtt5::mqtt_client<boost::asio::ip::tcp::socket> client(ioc);

        client.brokers("85.215.121.128", 1883).async_run(boost::asio::detached);

        async_mqtt5::subscribe_topic sub_topic = async_mqtt5::subscribe_topic{
                "ifc/test",
                async_mqtt5::subscribe_options {
                    async_mqtt5::qos_e::at_most_once,
                    async_mqtt5::no_local_e::no
                }};
        
        logfile << "subscribing" << std::endl;
        
        client.async_subscribe(
            sub_topic,
            async_mqtt5::subscribe_props{}, // Required properties
            [](async_mqtt5::error_code ec, std::vector<async_mqtt5::reason_code> reasons, async_mqtt5::suback_props) {
                if (ec) {
                    logfile << "Subscription Error: " << ec.message() << std::endl;
                } else {
                    logfile << "Subscribed successfully!" << std::endl;
                    receive_loop(client);
                }
            }
        );
        
        ioc.run();

    } catch (const std::exception& e) {
        logfile << "Exception in MQTT: " << GS::UniString(e.what());
    }
}

bool initialized = false;

GSErrCode Initialize (void)
{
    if(!initialized)
    {
        logfile.open("/Users/adrianhenke/logfile.txt", std::ios::app);
        mqttThread = std::make_unique<std::thread>(StartMqttClient);
        //initialized = true;
    }
    
#ifdef ServerMainVers_2700
    return ACAPI_MenuItem_InstallMenuHandler (AddOnMenuID, MenuCommandHandler);
#else
    return ACAPI_Install_MenuHandler (AddOnMenuID, MenuCommandHandler);
#endif
}

GSErrCode FreeData (void)
{
    running.store(false);
    ioc.stop();
    
    return NoError;
}

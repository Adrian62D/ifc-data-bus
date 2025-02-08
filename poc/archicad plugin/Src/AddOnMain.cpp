#include "APIEnvir.h"
#include "ACAPinc.h"

#include "ResourceIds.hpp"
#include "DGModule.hpp"
#include "APIdefs_Attributes.h"

#include <fstream>
#include <iostream>



void ListCompositeElementsToFile() {
    // Define the file dialog type and title
    //DG::FileDialog::Type dialogType = DG::FileDialog::Save;
    GS::UniString dialogTitle = "Save Composite Data";

    // Initialize the file dialog
    DG::FileDialog saveDialog(DG::FileDialog::Save);

    // Set the default file extension
    //saveDialog.AddFilter("CSV Files (*.csv)", "*.csv");

    // Show the dialog
    if (!saveDialog.Invoke()) {
        ACAPI_WriteReport("File selection cancelled by user.", true);
        return;
    }

    // Get the selected file path
    IO::Location fileLocation = saveDialog.GetSelectedFile();
    GS::UniString filePath = fileLocation.ToDisplayText();

    // Open the selected file for writing
    std::ofstream outFile(filePath.ToCStr().Get());
    if (!outFile.is_open()) {
        ACAPI_WriteReport("Failed to open the file for writing.", true);
        return;
    }

/*
    GSErrCode err;
    UInt32 nComposites = 0;

    // Step 1: Get the number of composites
    err = ACAPI_Attribute_GetNum(API_CompWallID, nComposites);
    if (err != NoError) {
        outFile << "Error retrieving number of composites: " << err << std::endl;
        return;
    }

    outFile << "Number of composites: " << nComposites << std::endl;

    // Step 2: Iterate through all composites
    for (Int32 index = 1; index <= nComposites; ++index) {
        API_Attribute compositeAttr;
        BNZeroMemory(&compositeAttr, sizeof(API_Attribute));
        compositeAttr.header.typeID = API_CompWallID;
        compositeAttr.header.index = ACAPI_CreateAttributeIndex(index);

        // Retrieve composite information
        err = ACAPI_Attribute_Get(&compositeAttr);
        if (err != NoError) {
            outFile << "Error retrieving composite at index " << index << ": " << err << std::endl;
            continue;
        }
        
        int x = APIERR_BADPARS;
        
        // Print the composite name
        outFile << "Composite " << index << ": " << compositeAttr.header.name << std::endl;
    }*/
    
    GSErrCode err;
    GS::Array<API_Attribute> compositeAttributes;
    
    // Step 1: Retrieve all composite attributes
    err = ACAPI_Attribute_GetAttributesByType(API_CompWallID, compositeAttributes);
    if (err != NoError) {
        outFile << "Error retrieving composites: " << err << std::endl;
        return;
    }

    // Step 2: Print the number of composites
    outFile << "Number of composites: " << compositeAttributes.GetSize() << std::endl;

    // Step 3: Iterate through composites
    for (UInt32 i = 0; i < compositeAttributes.GetSize(); ++i) {
        const API_Attribute& composite = compositeAttributes[i];
        outFile << "Composite " << (i + 1) << ": " << composite.header.name << std::endl;

        // Step 4: Retrieve composite definition to access layers
        API_AttributeDefExt    compositeDef;
        BNZeroMemory(&compositeDef, sizeof(API_AttributeDefExt));

        err = ACAPI_Attribute_GetDefExt (composite.header.typeID, composite.header.index, &compositeDef);
        if (err != NoError) {
            outFile << "  Error retrieving layers for composite: " << composite.header.name << " (" << err << ")" << std::endl;
            continue;
        }
        
        if (compositeDef.cwall_compItems != nullptr) {
            Int32 layerCount = BMGetHandleSize(reinterpret_cast<GSHandle>(compositeDef.cwall_compItems)) / sizeof(API_CWallComponent);
            for (Int32 i = 0; i < layerCount; ++i) {
                API_CWallComponent layer = (*compositeDef.cwall_compItems)[i];
                outFile << "  Layer " << (i + 1) << ": Thickness = " << layer.fillThick << std::endl;
                
                // Fetch material info
                API_Attribute material;
                BNZeroMemory(&material, sizeof(API_Attribute));
                material.header.typeID = API_BuildingMaterialID;  // Material attribute type
                material.header.index = layer.buildingMaterial;
                err = ACAPI_Attribute_Get(&material);
                if(err == NoError) {
                    GS::UniString materialName(material.header.name);
                    
                    //API_Attribute materialType;
                    //BNZeroMemory(&materialType, sizeof(API_Attribute));
                    //err = ACAPI_Attribute_Get(material.buildingMaterial., &materialType);
                    
                    if(err == NoError) {
                        outFile << "    Material " << materialName << ": Density = " << material.buildingMaterial.density << std::endl;
                        //ACAPI_DisposeAttrDefsHdlsExt(&materialProperty);
                    }
                    else {
                        outFile << "    Material " << materialName << ": x = (error) " << std::endl;
                    }
                }
                else {
                    outFile << "    Failed to fetch material for layer. Error code: " << err;
                }
            }
        }
        

        
/*
        // Step 5: Print layer details
        for (short layerIdx = 0; layerIdx < compositeDef.cwall_compItems; ++layerIdx) {
            const API_CompWallSkin& layer = compositeDef.skin[layerIdx];
            outFile << "  Layer " << (layerIdx + 1) << ": Thickness = " << layer.thickness
                      << ", Building Material Index = " << layer.buildingMaterial << std::endl;
        }
*/
        // Free memory allocated for the composite definition
        ACAPI_DisposeAttrDefsHdlsExt(&compositeDef);
    }

    outFile.close();
    ACAPI_WriteReport("Data successfully written to file.", true);
}


static const GSResID AddOnInfoID			= ID_ADDON_INFO;
	static const Int32 AddOnNameID			= 1;
	static const Int32 AddOnDescriptionID	= 2;

static const short AddOnMenuID				= ID_ADDON_MENU;
	static const Int32 AddOnCommandID		= 1;

class ExampleDialog :	public DG::ModalDialog,
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

			ListCompositeElementsToFile();

			PostCloseRequest (DG::ModalDialog::Accept);
		} else if (ev.GetSource () == &cancelButton) {
			PostCloseRequest (DG::ModalDialog::Cancel);
		}
	}

	DG::Button		okButton;
	DG::Button		cancelButton;
	DG::Separator	separator;
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

GSErrCode Initialize (void)
{
#ifdef ServerMainVers_2700
	return ACAPI_MenuItem_InstallMenuHandler (AddOnMenuID, MenuCommandHandler);
#else
	return ACAPI_Install_MenuHandler (AddOnMenuID, MenuCommandHandler);
#endif
}

GSErrCode FreeData (void)
{
	return NoError;
}

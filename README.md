# ifc data bus

This is a challenge of the **AEC Hackathon – Zurich Edition 2025**.

## Challenge

Architects and planners rely on various software tools. But, **poor data integration across tools creates bottlenecks** in the design process, hindering holistic project optimization.

OpenBIM currently lacks technologies for bi-directional data exchange, **particularly re-integrating data into CAD | CDE** is a challenge.

<img width="752" alt="image" src="https://github.com/user-attachments/assets/e5cadcd2-e32d-4324-bbe7-cfdef36df0f8" />

Limitations include: No near real-time data transfer or linking of data. Tracking of individual data fields is not possible. Authors for data fields cannot be assigned. Errors in the process due to manual transfer of information. And many other inefficiencies...

Since initiatives, such as Speckle, do not prioritize OpenBIM compliance, there is an opportunity to explore alternative approaches.

## Envisioned workflow

We envision a workflow with **publish-and-subscribe semantics**, built upon the **openBIM** standards IFC, IDS, bSDD to propagate model changes such as **buildups & materials** across an ecosystem of tools.

<img width="732" alt="image" src="https://github.com/user-attachments/assets/4b1fb25d-34a4-41ad-b7a7-5aa5b17ec788" />

## Let's create together

Let’s develop an openBIM-based **protocol** and a **proof of concept (PoC)** to exchange model updates in a distributed, bi-directional manner. The PoC will cover buildups, materials, classifications and/or building physics.

1. <a href="https://drive.google.com/file/d/1G6e2UCSyiQRj5Dxday6ytkK4VL-FCIHI/view?usp=sharing">Test IFC File</a>
2. <a href="https://drive.google.com/file/d/1Jvl45mIuUTdylNRtNFpbycbY55Tbuuml/view?usp=sharing">Archicad PLA File</a>
3. <a href="https://drive.google.com/file/d/1nhnUX_tlMNfOhmSC8T2DPsdUraAOrl_T/view?usp=sharing">Archicad PNL File</a>
4. <a href="https://drive.google.com/file/d/1nZ7oDA_LomUrPMGUZTA1sYswZqczJIdt/view?usp=sharing">Sequence Diagram</a>

# Outcome

## Overview

We managed to get **six clients** integrated on the PoC of the ifc data bus.

![1743660945307](https://github.com/user-attachments/assets/45c42016-b326-4e89-b9eb-6d6a1947ccaf)

## Demo

Short demo video of the PoC (click to play):

[![Watch the video](https://img.youtube.com/vi/StIqjEeKpnE/0.jpg)](https://www.youtube.com/watch?v=StIqjEeKpnE)

## Artefacts

- [ifcJSON Message Samples](https://github.com/Adrian62D/ifc-data-bus/tree/main/poc/message)
- [Grasshopper Client](https://github.com/Adrian62D/ifc-data-bus/tree/main/poc/grasshopper-client)
- [Web Client](https://github.com/Adrian62D/ifc-data-bus/tree/main/poc/web-client)
- [Blender Client](https://github.com/Adrian62D/ifc-data-bus/tree/main/poc/blender-client)
- [Archicad Client](https://github.com/Adrian62D/ifc-data-bus/tree/main/poc/archicad%20plugin)
- [MQTT Client](https://github.com/Adrian62D/ifc-data-bus/tree/main/poc/mqtt-client)

## Thanks! 

We've won at the hackathon in the category best-mashup-project. Thanks for your support!

# Next steps

- [x] Pitch at Hackathon
- [x] Pitch at BuildingSmart International
- [ ] Alignment with IFC5
- [ ] V0.1 of protocol



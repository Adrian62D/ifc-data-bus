# IFC Data bus

This project implements a data bus to communicate IFC data over a bus using publisher/subscriber communication patterns.

IFC data files are highly hierarchical. Transfering IFC data over a bus needs to correctly handle this hierarchy, and transfer data that is correlated (if needed).

This project aims at providing a solution that can used to collaborate of projects that use IFC data/files as a main source of geometric and semanatic data of a building.

## Architecture

The solution is based on a message bus architecture, utilizing the publisher/subscriber pattern.

The message bus is -initially- implemented using `compas_eve` with MQTT as transport layer. Other transport layers can be added to `compas_eve`.

The key contribution of this project is the data format of the IFC messages used in the system. Besides the actual IFC semantics, this project adds the changeset semantics, the ability of rebuilding an IFC as a tree of deltas (changesets) in the same way that git does it for code.

An open question is whether it would be recommendable to use CRDTs or not. Another question is whether is should support a layering strategy, as the USD file format supports.

The main reference client is implemented in Python, however, a C++ client also exists and other implementations could follow.

# Architecture & Design Pattern

This document describes the internal structure and design philosophy of the **pyFastPlot** application. It is intended to help developers and maintainers understand the overall context and codebase of the project.

## 1. Overview

Graphical User Interface (GUI) applications often suffer from tight coupling between UI presentation and business logic (data processing). Such coupling significantly reduces maintainability when UI components are updated or logic is modified. To prevent this, pyFastPlot adopts the **Model-View-Presenter (MVP)** design pattern.

## 2. MVP Architecture

The MVP pattern separates the software into three core components:

### Model (`src/pyfastplot/models/data_model.py`)
- **Role**: Manages data state and business logic.
- **Characteristics**: It does not import any UI-related packages (e.g., PySide6). This ensures that the Model can be reused even if the UI framework is replaced.
- **Responsibilities**: Reading CSV files, parsing clipboard data into 2D arrays, and handling missing values (NaN).

### View (`src/pyfastplot/views/`)
- **Role**: Renders the visual interface (buttons, tables, plots) and detects user interactions (clicks, drag-and-drop).
- **Characteristics**: Does not contain business logic. It emits events or signals and delegates processing to the Presenter.
- **Structure**:
  - `main_window.py`: Configures the overall layout of the application.
  - `components/`: Contains modular UI components such as tables and option panels.

### Presenter (`src/pyfastplot/presenters/main_presenter.py`)
- **Role**: Acts as a mediator between the Model and the View.
- **Characteristics**: Observes user events from the View, updates the data in the Model, and reflects the results back to the View to refresh the interface.
- **Responsibilities**: Controlling the application flow, validating data, and binding signals.

## 3. Data Flow

The following sequence illustrates the internal data flow during user interaction.

**Example: User clicks the [Plot] button**
1. **[View]**: The user clicks the `plot_button`, which emits a click signal.
2. **[Presenter]**: The `on_plot_data()` method, bound during initialization, is invoked.
3. **[Presenter]**: Retrieves the currently selected X and Y axis information from the View.
4. **[Presenter]**: Requests the corresponding numerical data (NumPy arrays) from the Model.
5. **[Presenter]**: Passes the retrieved data and plot options to the `MplCanvas` within the View for rendering.
6. **[View]**: Updates the Matplotlib canvas based on the received data.

## 4. Directory Structure

```text
pyFastPlot/
├── assets/                    # Static resources (Icons, Images)
├── docs/                      # Documentation (Architecture, etc.)
├── packaging/                 # Packaging & Distribution (NSIS)
├── scripts/                   # Utility scripts (Asset conversion)
├── src/
│   └── pyfastplot/            # Main application package
│       ├── __init__.py
│       ├── app.py             # Entry point: Assembles MVP components
│       ├── models/            # Data processing and state management
│       ├── presenters/        # Event coordination
│       └── views/             # UI components and layouts
├── main.py                    # Root entry point for execution
├── README.md                  # Project overview
└── requirements.txt           # Dependency list
```

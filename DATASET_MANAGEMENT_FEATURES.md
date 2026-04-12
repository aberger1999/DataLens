# Dataset Management & Save Features

## Features

### 1. Dataset Manager Dialog

A pop-out dialog accessible via the "Dataset Manager" button in the workspace header.

- View all datasets in the workspace with file size and last modified date
- Import new datasets from CSV files
- Load/switch between datasets with double-click or Load button
- Rename datasets via three-dots menu
- Delete datasets via three-dots menu with confirmation
- Active dataset highlighted in blue

**File:** `src/ui/components/dataset_manager_panel.py`

### 2. Unsaved Changes Tracking

The application tracks when data has been modified and not saved.

**Indicators:**
- Save button shows an asterisk and changes color when there are unsaved changes
- Returns to normal after saving

**Triggers:**
- Any preprocessing operation (remove columns, fill missing values, transform data, etc.)
- Any feature engineering operation (create features, encode categorical, extract datetime, etc.)

### 3. Save Workspace

Dedicated save button for workspace data.

- Saves current data to `workspace_data.csv` inside the workspace folder
- Clears unsaved changes indicator after successful save
- Shows success/error messages

### 4. Exit Confirmation Dialogs

Confirmation dialogs prevent accidental data loss when:

- **Switching datasets** - prompts to save before loading a different dataset
- **Going back to home** - prompts to save before leaving the workspace
- **Closing the application** - prompts to save before exiting

Options: Save then proceed, Discard changes, or Cancel.

## Workspace Header Layout

```
+-----------------------------------------------------------------------+
|  <- Back    Workspace Name    Dataset Manager   Import   Save         |
+-----------------------------------------------------------------------+
```

## Dataset Manager Dialog Layout

```
+-----------------------------------------------------------+
|  Manage Datasets                                          |
+-----------------------------------------------------------+
|                                                           |
|  +-----------------------------------------------------+ |
|  | workspace_data.csv                              ...  | | <- Active (Blue)
|  | 156.4 KB - 2025-02-02 14:30                          | |
|  +-----------------------------------------------------+ |
|  | Business_sales_EDA.csv                          ...  | |
|  | 6.2 MB - 2025-01-15 10:20                            | |
|  +-----------------------------------------------------+ |
|  | car_price_prediction.csv                        ...  | |
|  | 156.4 KB - 2025-01-10 08:45                          | |
|  +-----------------------------------------------------+ |
|                                                           |
|  [Import Dataset]                      [Load]  [Close]   |
+-----------------------------------------------------------+
```

## Technical Details

### Signal Flow

```
User Action (Preprocessing/Feature Engineering)
    |
data_modified signal emitted
    |
workspace_view.mark_unsaved_changes()
    |
has_unsaved_changes = True
    |
update_save_button() - Changes button appearance
```

### Dataset Loading Flow

```
User clicks Dataset Manager
    |
Dialog opens showing all datasets
    |
User selects dataset and clicks Load (or double-clicks)
    |
Check for unsaved changes
    | (if unsaved)
Show confirmation dialog
    | (if user confirms)
Save current data (optional)
    |
Load selected dataset
    |
Update active indicator
    |
Refresh data preview
```

## Files

### Created:
- `src/ui/components/dataset_manager_panel.py` - Dataset management dialog

### Modified:
- `src/ui/components/workspace_view.py` - Dialog-based dataset manager, unsaved changes tracking, save functionality, confirmation dialogs
- `src/ui/main_window.py` - closeEvent handler for exit confirmation
- `src/ui/components/preprocessing_panel.py` - data_modified signal
- `src/ui/components/feature_engineering_panel.py` - data_modified signal

## Notes

- `workspace_data.csv` is the working dataset and cannot be renamed
- Deleting a dataset is permanent
- All datasets are stored in `workspaces/workspace_X/data/`
- The dataset manager refreshes automatically when datasets change
- The dialog is modal - must be closed before returning to the workspace

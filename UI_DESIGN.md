# EasyOTP User Interface

## Main Window

The EasyOTP application features a clean, modern interface built with Flet.

### Layout

```
┌──────────────────────────────────────────────────┐
│  [Search...]                    [+]  [⋮]          │
├──────────────────────────────────────────────────┤
│                                                   │
│  ┌────────────────────────────────────────────┐  │
│  │ GitHub                        123 456      │  │
│  │ github.com                         25s     │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  ┌────────────────────────────────────────────┐  │
│  │ Google Account                654 321      │  │
│  │ Google                             18s     │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  ┌────────────────────────────────────────────┐  │
│  │ AWS Console                   789 012      │  │
│  │ Amazon Web Services                12s     │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  ┌────────────────────────────────────────────┐  │
│  │ Microsoft 365                 345 678      │  │
│  │ Microsoft                          5s      │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
└──────────────────────────────────────────────────┘
```

## Features

### Search Bar (Top)
- Initial focus when app opens
- Real-time filtering as you type
- Filters by account name or issuer
- Clear and immediate results

### Add Button (+)
Opens a dialog to add new OTP items:
- Name field (required)
- Secret key field (required) 
- Issuer field (optional)
- "Scan QR Code" button for importing from images

### Menu Button (⋮)
Dropdown menu with:
- Export - Save items to JSON file
- Import - Restore items from JSON file

### OTP Item Cards
Each card displays:
- **Top left**: Account name (bold)
- **Bottom left**: Issuer name (if provided, gray)
- **Top right**: 6-digit OTP code (large, monospace font)
- **Bottom right**: Countdown timer (seconds remaining)

### Interactions

#### Mouse
- **Click** on any item → Copy code to clipboard (shows notification)
- **Right-click/Long press** → Context menu with Edit/Delete options

#### Keyboard
- **Arrow Up/Down** → Navigate through items
- **Enter** → Copy selected item's code
- **Type in search** → Filter items in real-time

### Visual Feedback
- Selected item has blue highlight and border
- Copied items show green snackbar notification with code
- Codes update automatically every second
- Countdown shows remaining time until next code (30s cycle)

## Dialogs

### Add Item Dialog
```
┌──────────────────────────────────┐
│  Add OTP Item                    │
├──────────────────────────────────┤
│  Name: [____________]            │
│  Secret Key: [____________]      │
│  Issuer (optional): [_______]    │
│                                  │
│  [📷 Scan QR Code]               │
│                                  │
│           [Cancel]  [Add]        │
└──────────────────────────────────┘
```

### Edit Item Dialog
```
┌──────────────────────────────────┐
│  Edit OTP Item                   │
├──────────────────────────────────┤
│  Name: [GitHub________]          │
│  Secret Key: [JBSWY3D...]       │
│  Issuer (optional): [github.com] │
│                                  │
│           [Cancel]  [Save]       │
└──────────────────────────────────┘
```

### Delete Confirmation
```
┌──────────────────────────────────┐
│  Delete Item                     │
├──────────────────────────────────┤
│  Are you sure you want to        │
│  delete 'GitHub'?                │
│                                  │
│           [Cancel]  [Delete]     │
└──────────────────────────────────┘
```

### Context Menu (Right-click)
```
┌──────────────────────────────────┐
│  Actions for GitHub              │
├──────────────────────────────────┤
│  Edit                            │
│  Delete                          │
│  Cancel                          │
└──────────────────────────────────┘
```

## Color Scheme
- **Background**: Light gray (#F5F5F5)
- **Cards**: Light blue-gray (#E0E0E0)
- **Selected**: Blue (#BBDEFB) with blue border (#42A5F5)
- **Text**: Dark gray (#212121)
- **Secondary text**: Medium gray (#757575)
- **Codes**: Black, bold, monospace (Courier New)
- **Dark mode compatibility**: Text rendered on light card backgrounds uses dark foreground colors for readability

## Window Size
- Default width: 500px
- Default height: 700px
- Resizable to user preference

"""Main Flet UI application for EasyOTP."""
import flet as ft
import pyperclip
import time
import threading
import json
from typing import List, Optional, Tuple, Dict
from pathlib import Path

from easyotp.storage import Storage, OTPItem
from easyotp.otp import OTPGenerator
from easyotp.qr_scanner import QRScanner
from easyotp.qr_scanner import PYZBAR_AVAILABLE


# Window settings file path
WINDOW_SETTINGS_PATH = Path.home() / ".easyotp" / "window_settings.json"

# Minimum window dimensions
MIN_WINDOW_WIDTH = 400
MIN_WINDOW_HEIGHT = 300

# Maximum reasonable screen bounds for position validation
# These are conservative values to ensure window is visible on any monitor configuration
MAX_SCREEN_WIDTH = 8000
MAX_SCREEN_HEIGHT = 4000


def _safe_strip(value: str) -> str:
    """Safely strip leading and trailing whitespace from a string value."""
    return value.strip() if value else ""


def _is_dark_mode(page: ft.Page) -> bool:
    """Check if current page theme mode is dark."""
    if page.theme_mode == ft.ThemeMode.DARK:
        return True
    if page.theme_mode == ft.ThemeMode.LIGHT:
        return False
    platform_brightness = getattr(page, "platform_brightness", None)
    if platform_brightness is None:
        # Some Flet versions/platforms don't expose platform brightness.
        # Default to light mode instead of raising an error.
        return False

    brightness = getattr(ft, "Brightness", None)
    dark_brightness = getattr(brightness, "DARK", None) if brightness else None
    if dark_brightness is not None and platform_brightness == dark_brightness:
        return True

    # Fallback for versions that provide brightness as a plain string.
    return str(platform_brightness).strip().lower() == "dark"


class OTPListItem(ft.Container):
    """A single OTP item in the list."""
    
    def __init__(self, item: OTPItem, on_copy, on_edit, on_delete, on_show_secret, is_selected=False):
        super().__init__()
        self.otp_item = item
        self.on_copy = on_copy
        self.on_edit_callback = on_edit
        self.on_delete_callback = on_delete
        self.on_show_secret_callback = on_show_secret
        self.is_selected = is_selected
        
        self.code_text = ft.Text(
            value=self._get_code(),
            size=24,
            weight=ft.FontWeight.BOLD,
            font_family="Courier New"
        )
        
        self.name_text = ft.Text(
            value=item.name,
            size=16,
            weight=ft.FontWeight.W_500
        )
        
        self.issuer_text = ft.Text(
            value=item.issuer if item.issuer else "",
            size=12,
            color=ft.colors.GREY_700
        )
        
        # Create the row content
        row_content = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        self.name_text,
                        self.issuer_text,
                    ] if item.issuer else [self.name_text],
                    spacing=2,
                    expand=True
                ),
                ft.Column(
                    controls=[
                        self.code_text,
                    ],
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.END
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        
        # Wrap content in GestureDetector for right-click support
        self.content = ft.GestureDetector(
            content=row_content,
            on_tap=self._handle_click,
            on_secondary_tap=self._show_context_menu,
            on_long_press_start=self._show_context_menu,
        )
        
        self.padding = 15
        self.border_radius = 8
        self.ink = True
        self._update_background()
    
    def _update_background(self):
        """Update background color based on selection state."""
        is_dark_mode = _is_dark_mode(self.page) if self.page else False
        self.code_text.color = ft.colors.WHITE if is_dark_mode else ft.colors.BLACK
        self.name_text.color = ft.colors.WHITE if is_dark_mode else ft.colors.BLACK
        self.issuer_text.color = ft.colors.GREY_400 if is_dark_mode else ft.colors.GREY_700

        if self.is_selected:
            self.bgcolor = ft.colors.BLUE_900 if is_dark_mode else ft.colors.BLUE_100
            self.border = ft.border.all(2, ft.colors.BLUE_400)
        else:
            self.bgcolor = ft.colors.GREY_900 if is_dark_mode else ft.colors.GREY_100
            self.border = None

    def did_mount(self):
        """Apply theme-aware styling after control is attached to page."""
        self._update_background()
        self.update()
    
    def set_selected(self, selected: bool):
        """Set selection state."""
        self.is_selected = selected
        self._update_background()
        if self.page:
            self.update()
    
    def _get_code(self) -> str:
        """Get the current OTP code."""
        return OTPGenerator.generate_code(self.otp_item.secret)
    
    def update_code(self):
        """Update the displayed code."""
        self.code_text.value = self._get_code()
        if self.page:
            self.update()
    
    def _handle_click(self, e):
        """Handle click event."""
        self.on_copy(self)
    
    def _show_context_menu(self, e):
        """Show context menu on long press (right click alternative)."""
        self._open_menu(e)
    
    def _open_menu(self, e):
        """Open context menu."""
        if self.page:
            menu = ft.AlertDialog(
                title=ft.Text(f"Actions for {self.otp_item.name}"),
                content=ft.Column(
                    controls=[
                        ft.TextButton("Edit Name", on_click=lambda _: self._edit_name()),
                        ft.TextButton("Edit Issuer/Org", on_click=lambda _: self._edit_issuer()),
                        ft.TextButton("Update Secret", on_click=lambda _: self._edit_secret()),
                        ft.TextButton("Show Secret", on_click=lambda _: self._show_secret()),
                        ft.TextButton("Delete", on_click=lambda _: self._delete()),
                        ft.TextButton("Cancel", on_click=lambda _: self._close_menu()),
                    ],
                    tight=True,
                    spacing=0
                ),
            )
            self.page.dialog = menu
            menu.open = True
            self.page.update()
    
    def _edit_name(self):
        """Edit only the name."""
        self._close_menu()
        self.on_edit_callback(self.otp_item, "name")
    
    def _edit_issuer(self):
        """Edit only the issuer/org."""
        self._close_menu()
        self.on_edit_callback(self.otp_item, "issuer")
    
    def _edit_secret(self):
        """Edit only the secret."""
        self._close_menu()
        self.on_edit_callback(self.otp_item, "secret")
    
    def _delete(self):
        """Trigger delete callback."""
        self._close_menu()
        self.on_delete_callback(self.otp_item)
    
    def _show_secret(self):
        """Trigger show secret callback."""
        self._close_menu()
        self.on_show_secret_callback(self.otp_item)
    
    def _close_menu(self):
        """Close the context menu."""
        if self.page and self.page.dialog:
            self.page.dialog.open = False
            self.page.update()


class EasyOTPApp:
    """Main EasyOTP application."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "EasyOTP"
        
        # Set minimum window size
        self.page.window_min_width = MIN_WINDOW_WIDTH
        self.page.window_min_height = MIN_WINDOW_HEIGHT
        
        # Load and apply window settings
        self._load_window_settings()
        
        # Set up window resize and move handlers
        self.page.on_resize = self._on_window_resize
        self.page.on_window_event = self._on_window_event
        
        self.storage = Storage()
        self.items: List[OTPItem] = []
        self.list_items: List[OTPListItem] = []
        self.selected_index: Optional[int] = None
        
        # Global timer display
        self.global_timer_text = ft.Text(
            value=f"{OTPGenerator.get_remaining_seconds()}s",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLUE_700
        )
        
        self.search_field = ft.TextField(
            hint_text="Search...",
            autofocus=True,
            on_change=self._on_search_change,
            prefix_icon=ft.icons.SEARCH,
            expand=True
        )
        
        self.list_view = ft.ListView(
            expand=True,
            spacing=10,
            padding=10
        )
        
        self._setup_ui()
        self._load_items()
        self._start_timer_thread()
        
        # Set up keyboard handler
        self.page.on_keyboard_event = self._on_keyboard
    
    def _load_window_settings(self):
        """Load window position and size from settings file."""
        default_width = 500
        default_height = 700
        
        try:
            if WINDOW_SETTINGS_PATH.exists():
                with open(WINDOW_SETTINGS_PATH, 'r') as f:
                    settings = json.load(f)
                
                # Get screen dimensions (Flet doesn't provide this directly,
                # so we use reasonable defaults for validation)
                width = max(MIN_WINDOW_WIDTH, settings.get('width', default_width))
                height = max(MIN_WINDOW_HEIGHT, settings.get('height', default_height))
                left = settings.get('left', None)
                top = settings.get('top', None)
                
                # Apply size
                self.page.window_width = width
                self.page.window_height = height
                
                # Apply position if available and reasonable
                # Ensure window isn't positioned off-screen
                if left is not None and top is not None:
                    # Basic bounds check - ensure at least part of window is visible
                    # Use defined constants for maximum screen bounds
                    if left > -width + 100 and top > -height + 100 and left < MAX_SCREEN_WIDTH and top < MAX_SCREEN_HEIGHT:
                        self.page.window_left = left
                        self.page.window_top = top
                    else:
                        # Reset to center if position seems off-screen
                        self.page.window_center()
            else:
                self.page.window_width = default_width
                self.page.window_height = default_height
        except (json.JSONDecodeError, IOError, KeyError) as e:
            # Log error and use defaults if settings can't be loaded
            print(f"Note: Could not load window settings: {e}")
            self.page.window_width = default_width
            self.page.window_height = default_height
    
    def _save_window_settings(self):
        """Save window position and size to settings file."""
        try:
            settings = {
                'width': self.page.window_width,
                'height': self.page.window_height,
                'left': self.page.window_left,
                'top': self.page.window_top
            }
            WINDOW_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(WINDOW_SETTINGS_PATH, 'w') as f:
                json.dump(settings, f, indent=2)
        except (IOError, OSError) as e:
            # Log but don't crash if we can't save settings
            print(f"Note: Could not save window settings: {e}")
    
    def _on_window_resize(self, e):
        """Handle window resize events."""
        self._save_window_settings()
    
    def _on_window_event(self, e):
        """Handle window events (move, close, etc.)."""
        if e.data in ("moved", "close"):
            self._save_window_settings()
    
    def _setup_ui(self):
        """Set up the user interface."""
        import easyotp
        self._version = getattr(easyotp, "__version__", "unknown")
        
        # Timer container with icon
        timer_container = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.TIMER, size=16, color=ft.colors.BLUE_700),
                    self.global_timer_text,
                ],
                spacing=4,
            ),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=4,
            bgcolor=ft.colors.BLUE_50,
        )
        
        # Top bar with search and buttons
        top_bar = ft.Row(
            controls=[
                self.search_field,
                timer_container,
                ft.IconButton(
                    icon=ft.icons.ADD,
                    tooltip="Add Item",
                    on_click=self._show_add_dialog
                ),
                ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem(text="Export", on_click=self._export_items),
                        ft.PopupMenuItem(text="Import", on_click=self._import_items),
                        ft.PopupMenuItem(text="About", on_click=self._show_about_dialog),
                    ]
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        
        # Main content
        content = ft.Column(
            controls=[
                top_bar,
                ft.Divider(height=1),
                self.list_view
            ],
            expand=True,
            spacing=0
        )
        
        self.page.add(content)
    
    def _show_about_dialog(self, e=None):
        """Show About dialog with version and GitHub link."""
        dialog = ft.AlertDialog(
            title=ft.Text("About EasyOTP"),
            content=ft.Column([
                ft.Text(f"Version: {self._version}"),
                ft.Text("GitHub: ", size=14),
                ft.TextButton("https://github.com/raymondclowe/EasyOTP", url="https://github.com/raymondclowe/EasyOTP", style=ft.ButtonStyle(color=ft.colors.BLUE)),
            ], tight=True, spacing=8),
            actions=[ft.TextButton("Close", on_click=lambda _: self._close_dialog(dialog))]
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _load_items(self):
        """Load OTP items from storage."""
        self.items = self.storage.load_items()
        self._refresh_list()
    
    def _refresh_list(self, filter_text: str = ""):
        """Refresh the list view with filtered items."""
        self.list_view.controls.clear()
        self.list_items.clear()
        
        # Filter items
        filter_lower = filter_text.lower()
        filtered_items = [
            item for item in self.items
            if filter_lower in item.name.lower() or filter_lower in item.issuer.lower()
        ]
        
        # Create list items
        for i, item in enumerate(filtered_items):
            is_selected = (self.selected_index == i)
            list_item = OTPListItem(
                item=item,
                on_copy=self._copy_code,
                on_edit=self._edit_item,
                on_delete=self._confirm_delete,
                on_show_secret=self._show_secret,
                is_selected=is_selected
            )
            self.list_items.append(list_item)
            self.list_view.controls.append(list_item)
        
        # Reset selection if out of bounds
        if self.selected_index is not None and self.selected_index >= len(self.list_items):
            self.selected_index = None
        
        self.page.update()
    
    def _on_search_change(self, e):
        """Handle search field changes."""
        self.selected_index = None  # Reset selection when filtering
        self._refresh_list(self.search_field.value)
    
    def _copy_code(self, list_item: OTPListItem):
        """Copy the OTP code to clipboard."""
        code = OTPGenerator.generate_code(list_item.otp_item.secret)
        pyperclip.copy(code)
        
        # Update selection
        for i, item in enumerate(self.list_items):
            if item == list_item:
                self.selected_index = i
                item.set_selected(True)
            else:
                item.set_selected(False)
        
        # Show snackbar with prominent styling
        self.page.snack_bar = ft.SnackBar(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.WHITE, size=24),
                    ft.Text(
                        f"Code copied to clipboard: {code}",
                        color=ft.colors.WHITE,
                        size=16,
                        weight=ft.FontWeight.W_500
                    ),
                ],
                spacing=10,
            ),
            bgcolor=ft.colors.GREEN_700,
            duration=2000
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _on_keyboard(self, e: ft.KeyboardEvent):
        """Handle keyboard events."""
        if e.key == "Arrow Down":
            self._move_selection(1)
        elif e.key == "Arrow Up":
            self._move_selection(-1)
        elif e.key == "Enter":
            self._copy_selected()
    
    def _move_selection(self, delta: int):
        """Move selection up or down."""
        if not self.list_items:
            return
        
        if self.selected_index is None:
            self.selected_index = 0 if delta > 0 else len(self.list_items) - 1
        else:
            self.selected_index = (self.selected_index + delta) % len(self.list_items)
        
        # Update selection UI
        for i, item in enumerate(self.list_items):
            item.set_selected(i == self.selected_index)
    
    def _copy_selected(self):
        """Copy the code of the selected item."""
        if self.selected_index is not None and self.selected_index < len(self.list_items):
            self._copy_code(self.list_items[self.selected_index])
    
    def _show_add_dialog(self, e):
        """Show dialog to add a new item."""
        name_field = ft.TextField(label="Name", autofocus=True)
        secret_field = ft.TextField(label="Secret Key")
        issuer_field = ft.TextField(label="Issuer (optional)")
        
        qr_file_picker = ft.FilePicker(on_result=lambda e: self._handle_qr_file(e, name_field, secret_field, issuer_field))
        self.page.overlay.append(qr_file_picker)
        
        def add_item(e):
            secret = OTPGenerator.normalize_secret(secret_field.value)
            name = _safe_strip(name_field.value)
            issuer = _safe_strip(issuer_field.value)
            if name and secret:
                item = OTPItem(
                    name=name,
                    secret=secret,
                    issuer=issuer
                )
                self.storage.add_item(item)
                self._load_items()
                dialog.open = False
                self.page.update()
        
        qr_button = ft.ElevatedButton(
            "Scan QR Code",
            icon=ft.icons.QR_CODE_SCANNER,
            on_click=(
                (lambda _: qr_file_picker.pick_files(
                    allow_multiple=False,
                    allowed_extensions=["png", "jpg", "jpeg"]
                )) if PYZBAR_AVAILABLE else (lambda _: self._show_error("QR code scanning is not available. Required library (pyzbar) or DLL is missing."))
            ),
            disabled=not PYZBAR_AVAILABLE
        )
        dialog = ft.AlertDialog(
            title=ft.Text("Add OTP Item"),
            content=ft.Column(
                controls=[
                    name_field,
                    secret_field,
                    issuer_field,
                    qr_button
                ],
                tight=True,
                spacing=10
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dialog)),
                ft.TextButton("Add", on_click=add_item)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _handle_qr_file(self, e: ft.FilePickerResultEvent, name_field, secret_field, issuer_field):
        """Handle QR code file selection."""
        if e.files:
            filepath = e.files[0].path
            uri = QRScanner.scan_from_file(filepath)
            if uri:
                parsed = OTPGenerator.parse_otpauth_uri(uri)
                if parsed:
                    name_field.value = parsed["name"]
                    secret_field.value = parsed["secret"]
                    issuer_field.value = parsed["issuer"]
                    self.page.update()
                else:
                    self._show_error("Could not parse QR code")
            else:
                self._show_error("No OTP QR code found in image")
    
    def _edit_item(self, item: OTPItem, field: str = "all"):
        """Show dialog to edit an item. Field can be 'all', 'name', 'issuer', or 'secret'."""
        if field == "name":
            # Edit only name
            name_field = ft.TextField(label="Name", value=item.name, autofocus=True)
            
            def save_name(e):
                name = _safe_strip(name_field.value)
                if name:
                    new_item = OTPItem(
                        name=name,
                        secret=item.secret,
                        issuer=item.issuer
                    )
                    self.storage.update_item(item.name, new_item)
                    self._load_items()
                    dialog.open = False
                    self.page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text("Edit Name"),
                content=ft.Column(controls=[name_field], tight=True, spacing=10),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dialog)),
                    ft.TextButton("Save", on_click=save_name)
                ]
            )
        elif field == "issuer":
            # Edit only issuer/org
            issuer_field = ft.TextField(label="Issuer/Organization", value=item.issuer, autofocus=True)
            
            def save_issuer(e):
                issuer = _safe_strip(issuer_field.value)
                new_item = OTPItem(
                    name=item.name,
                    secret=item.secret,
                    issuer=issuer
                )
                self.storage.update_item(item.name, new_item)
                self._load_items()
                dialog.open = False
                self.page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text("Edit Issuer/Organization"),
                content=ft.Column(controls=[issuer_field], tight=True, spacing=10),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dialog)),
                    ft.TextButton("Save", on_click=save_issuer)
                ]
            )
        elif field == "secret":
            # Edit only secret
            secret_field = ft.TextField(label="Secret Key", value=item.secret, autofocus=True)
            
            def save_secret(e):
                secret = OTPGenerator.normalize_secret(secret_field.value)
                if secret:
                    new_item = OTPItem(
                        name=item.name,
                        secret=secret,
                        issuer=item.issuer
                    )
                    self.storage.update_item(item.name, new_item)
                    self._load_items()
                    dialog.open = False
                    self.page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text("Update Secret"),
                content=ft.Column(controls=[secret_field], tight=True, spacing=10),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dialog)),
                    ft.TextButton("Save", on_click=save_secret)
                ]
            )
        else:
            # Edit all fields
            name_field = ft.TextField(label="Name", value=item.name, autofocus=True)
            secret_field = ft.TextField(label="Secret Key", value=item.secret)
            issuer_field = ft.TextField(label="Issuer (optional)", value=item.issuer)
            
            def save_item(e):
                secret = OTPGenerator.normalize_secret(secret_field.value)
                name = _safe_strip(name_field.value)
                issuer = _safe_strip(issuer_field.value)
                if name and secret:
                    new_item = OTPItem(
                        name=name,
                        secret=secret,
                        issuer=issuer
                    )
                    self.storage.update_item(item.name, new_item)
                    self._load_items()
                    dialog.open = False
                    self.page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text("Edit OTP Item"),
                content=ft.Column(
                    controls=[name_field, secret_field, issuer_field],
                    tight=True,
                    spacing=10
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dialog)),
                    ft.TextButton("Save", on_click=save_item)
                ]
            )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _show_secret(self, item: OTPItem):
        """Show dialog displaying the secret key."""
        is_dark_mode = _is_dark_mode(self.page)
        dialog = ft.AlertDialog(
            title=ft.Text(f"Secret for {item.name}"),
            content=ft.Column(
                controls=[
                    ft.Text("Secret Key:", size=12, color=ft.colors.GREY_400 if is_dark_mode else ft.colors.GREY_700),
                    ft.Container(
                        content=ft.Text(
                            item.secret,
                            font_family="Courier New",
                            size=14,
                            color=ft.colors.WHITE if is_dark_mode else ft.colors.BLACK,
                            selectable=True
                        ),
                        bgcolor=ft.colors.GREY_900 if is_dark_mode else ft.colors.GREY_100,
                        padding=10,
                        border_radius=4,
                    ),
                    ft.Text(
                        "⚠️ Keep this secret safe and don't share it!",
                        size=12,
                        color=ft.colors.ORANGE_400 if is_dark_mode else ft.colors.ORANGE_700,
                        italic=True
                    ),
                ],
                tight=True,
                spacing=10
            ),
            actions=[
                ft.TextButton("Copy", on_click=lambda _: self._copy_secret_to_clipboard(item.secret)),
                ft.TextButton("Close", on_click=lambda _: self._close_dialog(dialog))
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _copy_secret_to_clipboard(self, secret: str):
        """Copy secret to clipboard."""
        pyperclip.copy(secret)
        self.page.snack_bar = ft.SnackBar(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.WHITE, size=24),
                    ft.Text("Secret copied to clipboard", color=ft.colors.WHITE, size=16),
                ],
                spacing=10,
            ),
            bgcolor=ft.colors.BLUE_700,
            duration=2000
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _confirm_delete(self, item: OTPItem):
        """Show confirmation dialog before deleting."""
        def delete(e):
            self.storage.delete_item(item.name)
            self._load_items()
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Delete Item"),
            content=ft.Text(f"Are you sure you want to delete '{item.name}'?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dialog)),
                ft.TextButton("Delete", on_click=delete)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _export_items(self, e):
        """Export items to JSON file."""
        file_picker = ft.FilePicker(on_result=self._handle_export_file)
        self.page.overlay.append(file_picker)
        self.page.update()
        file_picker.save_file(
            dialog_title="Export OTP Items",
            file_name="otp_export.json",
            allowed_extensions=["json"]
        )
    
    def _handle_export_file(self, e: ft.FilePickerResultEvent):
        """Handle export file selection."""
        if e.path:
            try:
                self.storage.export_to_json(e.path)
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Items exported successfully!"),
                    duration=2000
                )
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as ex:
                self._show_error(f"Export failed: {ex}")
    
    def _import_items(self, e):
        """Import items from JSON file."""
        file_picker = ft.FilePicker(on_result=self._handle_import_file)
        self.page.overlay.append(file_picker)
        self.page.update()
        file_picker.pick_files(
            dialog_title="Import OTP Items",
            allowed_extensions=["json"],
            allow_multiple=False
        )
    
    @staticmethod
    def _merge_fields(field1: str, field2: str) -> str:
        """Merge two field values, handling empty strings properly."""
        # If both are the same, return one
        if field1 == field2:
            return field1 or field2
        
        # If one is empty, return the other
        if not field1:
            return field2
        if not field2:
            return field1
        
        # Both are different and non-empty, concatenate
        return f"{field1} / {field2}"
    
    def _handle_import_file(self, e: ft.FilePickerResultEvent):
        """Handle import file selection."""
        if e.files:
            try:
                items_to_add, conflicts = self.storage.import_from_json(e.files[0].path)
                
                # If there are conflicts, show resolution dialog
                if conflicts:
                    self._show_conflict_resolution_dialog(items_to_add, conflicts)
                else:
                    # No conflicts, just add items
                    if items_to_add:
                        self.storage.add_items(items_to_add)
                        self._load_items()
                        self.page.snack_bar = ft.SnackBar(
                            content=ft.Text(f"Imported {len(items_to_add)} item(s) successfully!"),
                            duration=2000
                        )
                        self.page.snack_bar.open = True
                        self.page.update()
                    else:
                        self.page.snack_bar = ft.SnackBar(
                            content=ft.Text("No new items to import (all duplicates skipped)."),
                            duration=2000
                        )
                        self.page.snack_bar.open = True
                        self.page.update()
            except Exception as ex:
                self._show_error(f"Import failed: {ex}")
    
    def _show_conflict_resolution_dialog(self, items_to_add: List[OTPItem], conflicts: List[Tuple[OTPItem, OTPItem]]):
        """Show dialog for resolving import conflicts."""
        # Store decisions for each conflict
        conflict_decisions: Dict[int, str] = {}
        
        def handle_dismiss(e):
            """Handle dialog dismissal - default to keep existing and continue."""
            if len(conflict_decisions) < len(conflicts):
                # User dismissed without making a decision, default to keep_existing
                current_index = len(conflict_decisions)
                conflict_decisions[current_index] = "keep_existing"
                show_conflict(current_index + 1)
        
        def show_conflict(index):
            """Show conflict at given index."""
            if index >= len(conflicts):
                # All conflicts resolved, process decisions
                self._process_conflict_decisions(items_to_add, conflicts, conflict_decisions)
                return
            
            existing_item, new_item = conflicts[index]
            
            # Create preview of both items
            existing_preview = ft.Column([
                ft.Text("Existing Item:", weight=ft.FontWeight.BOLD, size=14),
                ft.Text(f"Name: {existing_item.name}", size=12),
                ft.Text(f"Issuer: {existing_item.issuer or '(none)'}", size=12),
                ft.Text(f"Secret: {existing_item.secret[:10]}...", size=12, color=ft.colors.GREY_600),
            ], spacing=5)
            
            new_preview = ft.Column([
                ft.Text("Import Item:", weight=ft.FontWeight.BOLD, size=14),
                ft.Text(f"Name: {new_item.name}", size=12),
                ft.Text(f"Issuer: {new_item.issuer or '(none)'}", size=12),
                ft.Text(f"Secret: {new_item.secret[:10]}...", size=12, color=ft.colors.GREY_600),
            ], spacing=5)
            
            merged_name = self._merge_fields(existing_item.name, new_item.name)
            merged_issuer = self._merge_fields(existing_item.issuer, new_item.issuer)
            
            merged_preview = ft.Column([
                ft.Text("Merged Result:", weight=ft.FontWeight.BOLD, size=14),
                ft.Text(f"Name: {merged_name}", size=12),
                ft.Text(f"Issuer: {merged_issuer or '(none)'}", size=12),
                ft.Text(f"Secret: {existing_item.secret[:10]}...", size=12, color=ft.colors.GREY_600),
            ], spacing=5)
            
            def handle_keep_existing(e):
                conflict_decisions[index] = "keep_existing"
                dialog.open = False
                self.page.update()
                show_conflict(index + 1)
            
            def handle_keep_new(e):
                conflict_decisions[index] = "keep_new"
                dialog.open = False
                self.page.update()
                show_conflict(index + 1)
            
            def handle_merge(e):
                conflict_decisions[index] = "merge"
                dialog.open = False
                self.page.update()
                show_conflict(index + 1)
            
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Duplicate Secret Detected ({index + 1} of {len(conflicts)})"),
                content=ft.Column([
                    ft.Text("The same secret exists with different name/issuer fields.", size=13),
                    ft.Divider(),
                    existing_preview,
                    ft.Divider(),
                    new_preview,
                    ft.Divider(),
                    merged_preview,
                ], tight=True, scroll=ft.ScrollMode.AUTO, height=400),
                actions=[
                    ft.TextButton("Keep Existing", on_click=handle_keep_existing),
                    ft.TextButton("Keep Import", on_click=handle_keep_new),
                    ft.TextButton("Merge", on_click=handle_merge),
                ],
                actions_alignment=ft.MainAxisAlignment.SPACE_AROUND,
                on_dismiss=handle_dismiss,
            )
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
        
        # Start showing conflicts
        show_conflict(0)
    
    def _process_conflict_decisions(self, items_to_add: List[OTPItem], conflicts: List[Tuple[OTPItem, OTPItem]], decisions: Dict[int, str]):
        """Process conflict resolution decisions and update storage."""
        items_to_replace = []
        
        for index, (existing_item, new_item) in enumerate(conflicts):
            decision = decisions.get(index, "keep_existing")
            
            if decision == "keep_existing":
                # Do nothing, keep existing
                pass
            elif decision == "keep_new":
                # Replace existing with new (by secret to ensure correct item is replaced)
                items_to_replace.append((existing_item.secret, new_item))
            elif decision == "merge":
                # Create merged item
                merged_name = self._merge_fields(existing_item.name, new_item.name)
                merged_issuer = self._merge_fields(existing_item.issuer, new_item.issuer)
                merged_item = OTPItem(
                    name=merged_name,
                    secret=existing_item.secret,
                    issuer=merged_issuer
                )
                items_to_replace.append((existing_item.secret, merged_item))
        
        # Apply replacements by secret to ensure correct item is replaced
        for secret, new_item in items_to_replace:
            self.storage.update_item_by_secret(secret, new_item)
        
        # Add non-conflicting items
        if items_to_add:
            self.storage.add_items(items_to_add)
        
        # Reload and show success message
        self._load_items()
        total_imported = len(items_to_add) + sum(1 for d in decisions.values() if d in ["keep_new", "merge"])
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Import complete! {total_imported} item(s) processed."),
            duration=2000
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _close_dialog(self, dialog):
        """Close a dialog."""
        dialog.open = False
        self.page.update()
    
    def _show_error(self, message: str):
        """Show an error message."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            duration=3000,
            bgcolor=ft.colors.RED_400
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _start_timer_thread(self):
        """Start a background thread to update codes and global timer."""
        def update_codes():
            last_period = -1
            while True:
                try:
                    # Get current 30-second period
                    current_period = int(time.time()) // 30
                    
                    # Only update codes when we enter a new 30-second period
                    if current_period != last_period:
                        last_period = current_period
                        for list_item in self.list_items:
                            try:
                                list_item.update_code()
                            except Exception:
                                pass  # Skip items that fail to update
                    
                    # Update global timer display every second
                    remaining = OTPGenerator.get_remaining_seconds()
                    self.global_timer_text.value = f"{remaining}s"
                    if self.global_timer_text.page:
                        self.global_timer_text.update()
                except Exception:
                    pass  # Continue the timer thread even if an update fails
                
                time.sleep(1)
        
        thread = threading.Thread(target=update_codes, daemon=True)
        thread.start()


def main():
    """Main entry point."""
    ft.app(target=lambda page: EasyOTPApp(page))


if __name__ == "__main__":
    main()

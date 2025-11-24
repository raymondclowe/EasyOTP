"""Main Flet UI application for EasyOTP."""
import flet as ft
import pyperclip
import time
import threading
from typing import List, Optional
from pathlib import Path

from .storage import Storage, OTPItem
from .otp import OTPGenerator
from .qr_scanner import QRScanner


class OTPListItem(ft.Container):
    """A single OTP item in the list."""
    
    def __init__(self, item: OTPItem, on_copy, on_edit, on_delete, is_selected=False):
        super().__init__()
        self.otp_item = item
        self.on_copy = on_copy
        self.on_edit_callback = on_edit
        self.on_delete_callback = on_delete
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
            color=ft.colors.GREY_600
        )
        
        self.timer_text = ft.Text(
            value=f"{OTPGenerator.get_remaining_seconds()}s",
            size=14,
            color=ft.colors.GREY_700
        )
        
        self.content = ft.Row(
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
                        ft.Row(
                            controls=[self.timer_text],
                            alignment=ft.MainAxisAlignment.END
                        )
                    ],
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.END
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        
        self.padding = 15
        self.border_radius = 8
        self.on_click = self._handle_click
        self.on_long_press = self._show_context_menu
        self.ink = True
        self._update_background()
    
    def _update_background(self):
        """Update background color based on selection state."""
        if self.is_selected:
            self.bgcolor = ft.colors.BLUE_100
            self.border = ft.border.all(2, ft.colors.BLUE_400)
        else:
            self.bgcolor = ft.colors.GREY_100
            self.border = None
    
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
        """Update the displayed code and timer."""
        self.code_text.value = self._get_code()
        self.timer_text.value = f"{OTPGenerator.get_remaining_seconds()}s"
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
                        ft.TextButton("Edit", on_click=lambda _: self._edit()),
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
    
    def _edit(self):
        """Trigger edit callback."""
        self._close_menu()
        self.on_edit_callback(self.otp_item)
    
    def _delete(self):
        """Trigger delete callback."""
        self._close_menu()
        self.on_delete_callback(self.otp_item)
    
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
        self.page.window_width = 500
        self.page.window_height = 700
        
        self.storage = Storage()
        self.items: List[OTPItem] = []
        self.list_items: List[OTPListItem] = []
        self.selected_index: Optional[int] = None
        
        self.search_field = ft.TextField(
            hint_text="Search...",
            autofocus=True,
            on_change=self._on_search_change,
            prefix_icon=ft.icons.SEARCH
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
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Top bar with search and buttons
        top_bar = ft.Row(
            controls=[
                self.search_field,
                ft.IconButton(
                    icon=ft.icons.ADD,
                    tooltip="Add Item",
                    on_click=self._show_add_dialog
                ),
                ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem(text="Export", on_click=self._export_items),
                        ft.PopupMenuItem(text="Import", on_click=self._import_items),
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
        
        # Show snackbar
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Copied {list_item.otp_item.name}: {code}"),
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
            if name_field.value and secret:
                item = OTPItem(
                    name=name_field.value,
                    secret=secret,
                    issuer=issuer_field.value
                )
                self.storage.add_item(item)
                self._load_items()
                dialog.open = False
                self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Add OTP Item"),
            content=ft.Column(
                controls=[
                    name_field,
                    secret_field,
                    issuer_field,
                    ft.ElevatedButton(
                        "Scan QR Code",
                        icon=ft.icons.QR_CODE_SCANNER,
                        on_click=lambda _: qr_file_picker.pick_files(
                            allow_multiple=False,
                            allowed_extensions=["png", "jpg", "jpeg"]
                        )
                    )
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
    
    def _edit_item(self, item: OTPItem):
        """Show dialog to edit an item."""
        name_field = ft.TextField(label="Name", value=item.name, autofocus=True)
        secret_field = ft.TextField(label="Secret Key", value=item.secret)
        issuer_field = ft.TextField(label="Issuer (optional)", value=item.issuer)
        
        def save_item(e):
            secret = OTPGenerator.normalize_secret(secret_field.value)
            if name_field.value and secret:
                new_item = OTPItem(
                    name=name_field.value,
                    secret=secret,
                    issuer=issuer_field.value
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
    
    def _handle_import_file(self, e: ft.FilePickerResultEvent):
        """Handle import file selection."""
        if e.files:
            try:
                self.storage.import_from_json(e.files[0].path)
                self._load_items()
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Items imported successfully!"),
                    duration=2000
                )
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as ex:
                self._show_error(f"Import failed: {ex}")
    
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
        """Start a background thread to update codes."""
        def update_codes():
            while True:
                time.sleep(1)
                for list_item in self.list_items:
                    list_item.update_code()
        
        thread = threading.Thread(target=update_codes, daemon=True)
        thread.start()


def main():
    """Main entry point."""
    ft.app(target=lambda page: EasyOTPApp(page))


if __name__ == "__main__":
    main()

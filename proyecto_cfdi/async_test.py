
import flet as ft
import asyncio

async def main(page: ft.Page):
    page.title = "Prueba ASYNC FilePicker"
    
    def on_dialog_result(e):
        print(f"Resultado: {e.path}")
        if e.path:
            t.value = f"Seleccionado: {e.path}"
        else:
            t.value = "Cancelado"
        page.update()

    file_picker = ft.FilePicker()
    file_picker.on_result = on_dialog_result
    page.overlay.append(file_picker)
    page.update()

    async def open_picker(e):
        print("Botón presionado (Async).")
        try:
            print("Llamando await get_directory_path...")
            await file_picker.get_directory_path(dialog_title="Prueba Async")
            print("Retorno de await.")
        except Exception as ex:
            print(f"Error: {ex}")

    b = ft.ElevatedButton("Seleccionar Carpeta (Async)", on_click=open_picker)
    t = ft.Text("Nada seleccionado")

    page.add(b, t)

if __name__ == "__main__":
    ft.app(target=main)

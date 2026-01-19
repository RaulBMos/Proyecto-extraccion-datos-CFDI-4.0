
import flet as ft
import asyncio

async def main(page: ft.Page):
    page.title = "Test FilePicker"
    
    def on_dialog_result(e):
        print("RESULTADO:", e.path)
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
        print("Abriendo picker...")
        try:
            # Intentamos con await
            await file_picker.get_directory_path()
            print("Await exitoso")
        except AttributeError:
             print("get_directory_path_async no existe, probando sync/normal")
             try:
                # Si falla, probamos get_directory_path (que podría ser awaitable o no)
                res = file_picker.get_directory_path()
                if asyncio.iscoroutine(res):
                    await res
                    print("Await en get_directory_path exitoso")
                else:
                    print("Llamada síncrona exitosa")
             except Exception as ex:
                 print(f"Error al abrir: {ex}")
        except Exception as ex:
            print(f"Error general: {ex}")

    b = ft.ElevatedButton("Seleccionar Carpeta", on_click=open_picker)
    t = ft.Text("Nada seleccionado")

    page.add(b, t)

if __name__ == "__main__":
    ft.app(target=main)

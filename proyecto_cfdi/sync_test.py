
import flet as ft

def main(page: ft.Page):
    page.title = "Prueba Síncrona FilePicker"

    def on_dialog_result(e):
        print(f"Resultado FilePicker: {e.path}")
        if e.path:
            txt_result.value = f"Carpeta: {e.path}"
        else:
            txt_result.value = "Cancelado"
        page.update()

    file_picker = ft.FilePicker()
    file_picker.on_result = on_dialog_result
    page.overlay.append(file_picker)

    def select_folder(e):
        print("Botón presionado. Llamando get_directory_path()...")
        file_picker.get_directory_path(dialog_title="Selecciona una carpeta")
        print("Llamada finalizada.")

    btn = ft.ElevatedButton("Seleccionar Carpeta", on_click=select_folder)
    txt_result = ft.Text("Nada seleccionado")

    page.add(
        ft.Text("Prueba de FilePicker Síncrono", size=20),
        btn,
        txt_result
    )
    page.update()

if __name__ == "__main__":
    print("Iniciando app...")
    ft.app(target=main)

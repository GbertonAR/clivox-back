import os
import argparse

def generate_dir_structure(root_dir, output_file, exclude_dirs=None):
    """
    Genera la estructura de directorios y archivos de un proyecto,
    excluyendo directorios específicos, y la guarda en un archivo.

    Args:
        root_dir (str): La ruta raíz del proyecto.
        output_file (str): El nombre del archivo donde se guardará la estructura.
        exclude_dirs (list): Una lista de nombres de directorios a excluir.
    """
    if exclude_dirs is None:
        exclude_dirs = []

    # Abrimos el archivo de salida para escribir la estructura
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Estructura del proyecto: {os.path.abspath(root_dir)}\n")
        f.write("-" * 50 + "\n\n")

        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Calculamos la profundidad actual para la indentación
            # Esto ayuda a visualizar la jerarquía como un árbol
            depth = dirpath.count(os.sep) - root_dir.count(os.sep)
            indent = '    ' * depth # 4 espacios por nivel

            # Filtramos los directorios que se deben excluir de dirnames
            # Esto evita que os.walk entre en ellos
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

            # Escribimos el directorio actual
            if depth == 0: # El directorio raíz no tiene prefijo de indentación
                f.write(f"{os.path.basename(dirpath)}/\n")
            else:
                f.write(f"{indent[:-4]}├── {os.path.basename(dirpath)}/\n") # Ajuste para el primer subdirectorio
                
            # Escribimos los archivos del directorio actual
            for filename in filenames:
                f.write(f"{indent}├── {filename}\n") # Los archivos tienen la indentación completa

            # Si es el directorio raíz y está vacío de archivos/directorios visibles,
            # pero el os.walk nos da un 'dirpath' de un subdirectorio,
            # necesitamos ajustar la indentación para el siguiente nivel.
            # Esta lógica es más simple si solo imprimimos y filtramos.

    print(f"Estructura del directorio generada en: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Genera la estructura de directorios de un proyecto, excluyendo directorios específicos."
    )
    parser.add_argument(
        "root_directory",
        nargs="?", # Hace que el argumento sea opcional
        default=os.getcwd(), # Por defecto, usa el directorio actual
        help="La ruta raíz del proyecto (por defecto, el directorio actual)."
    )
    parser.add_argument(
        "-o", "--output",
        default="project_structure.txt",
        help="Nombre del archivo de salida (por defecto, project_structure.txt)."
    )
    parser.add_argument(
        "-e", "--exclude",
        nargs='*', # Permite 0 o más valores
        default=['.git', '__pycache__', 'venv', 'node_modules', '.vscode', '.idea', 'dist', 'build', '.pytest_cache'],
        help="Lista de directorios a excluir (separados por espacios)."
    )

    args = parser.parse_args()

    # Si la ruta raíz proporcionada no existe, se usa el directorio actual
    if not os.path.isdir(args.root_directory):
        print(f"Advertencia: La ruta '{args.root_directory}' no existe. Usando el directorio actual.")
        args.root_directory = os.getcwd()

    generate_dir_structure(args.root_directory, args.output, args.exclude)
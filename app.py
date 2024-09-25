import tempfile
import requests
import zipfile
import os
import lizard
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    repo_url = data.get('repoUrl')
    
    if not repo_url:
        return jsonify({"error": "No se proporcionó el enlace del repositorio"}), 400
    
    try:
        # Detectar la URL correcta del repositorio
        if repo_url.endswith('.git'):
            repo_url = repo_url[:-4]  # Eliminar la extensión .git

        # Probar con la rama 'main' y 'master' si la 'main' no existe
        download_urls = [
            f"{repo_url}/archive/refs/heads/main.zip",
            f"{repo_url}/archive/refs/heads/master.zip"
        ]
        
        response = None
        for url in download_urls:
            response = requests.get(url)
            if response.status_code == 200:
                break
        else:
            return jsonify({"error": "Error al descargar el repositorio"}), 500

        # Crear un directorio temporal y extraer el archivo ZIP
        with tempfile.TemporaryDirectory() as tmpdirname:
            zip_path = os.path.join(tmpdirname, 'repo.zip')
            with open(zip_path, 'wb') as zip_file:
                zip_file.write(response.content)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdirname)

            # Obtener el directorio extraído
            extracted_dir = os.path.join(tmpdirname, os.listdir(tmpdirname)[0])

            # Extensiones compatibles, puedes añadir más si lo consideras necesario
            extensions = ['.cs', '.java', '.js', '.ts', '.kts', '.py', '.rb', '.cpp', '.c', '.php', '.go', '.rs']
            results = []

            # Analizar todos los archivos dentro del directorio extraído
            found_files = False  # Flag para saber si se encontraron archivos con extensiones compatibles
            for root, _, files in os.walk(extracted_dir):  # Ahora recorremos todo el directorio recursivamente
                for file in files:
                    if any(file.endswith(ext) for ext in extensions):
                        found_files = True  # Se encontraron archivos compatibles
                        file_path = os.path.join(root, file)
                        analysis = lizard.analyze_file(file_path)
                        
                        for func in analysis.function_list:
                            results.append({
                                "file": file_path,
                                "function_name": func.name,
                                "nloc": func.nloc,
                                "cyclomatic_complexity": func.cyclomatic_complexity,
                                "token_count": func.token_count,
                            })

            # Comprobar si se encontraron archivos compatibles para analizar
            if not found_files:
                return jsonify({"error": "No se encontraron archivos de código fuente compatibles para analizar"}), 400
            
            # Devolver el resultado del análisis
            return jsonify({"metrics": results})

    except Exception as e:
        return jsonify({"error": "Error al procesar el repositorio", "details": str(e)}), 500

if __name__ == '__main__':
    app.run()

import tempfile
import requests
import zipfile
import os
import lizard
from flask import Flask, request, jsonify
import logging

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    repo_url = data.get('repoUrl')
    
    if not repo_url:
        return jsonify({"error": "No se proporcionó el enlace del repositorio"}), 400
    
    try:
        if repo_url.endswith('.git'):
            repo_url = repo_url[:-4]

        download_urls = [
            f"{repo_url}/archive/refs/heads/main.zip",
            f"{repo_url}/archive/refs/heads/master.zip"
        ]
        
        response = None
        for url in download_urls:
            logging.debug(f"Intentando descargar el repositorio desde: {url}")
            response = requests.get(url)
            if response.status_code == 200:
                logging.debug(f"Descarga exitosa desde: {url}")
                break
        else:
            return jsonify({"error": "Error al descargar el repositorio"}), 500

        with tempfile.TemporaryDirectory() as tmpdirname:
            zip_path = os.path.join(tmpdirname, 'repo.zip')
            with open(zip_path, 'wb') as zip_file:
                zip_file.write(response.content)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdirname)

            extracted_dir = os.path.join(tmpdirname, os.listdir(tmpdirname)[0])
            logging.debug(f"Directorio extraído: {extracted_dir}")

            extensions = ['.cs', '.java', '.js', '.ts', '.kts', '.py', '.rb', '.cpp', '.c', '.php', '.go', '.rs']
            results = []

            found_files = False 
            for root, _, files in os.walk(extracted_dir): 
                logging.debug(f"Revisando directorio: {root}")
                for file in files:
                    logging.debug(f"Archivo encontrado: {file}")
                    if any(file.endswith(ext) for ext in extensions):
                        found_files = True  
                        file_path = os.path.join(root, file)
                        logging.debug(f"Analizando archivo: {file_path}")
                        analysis = lizard.analyze_file(file_path)
                        
                        for func in analysis.function_list:
                            results.append({
                                "file": file_path,
                                "function_name": func.name,
                                "nloc": func.nloc,
                                "cyclomatic_complexity": func.cyclomatic_complexity,
                                "token_count": func.token_count,
                            })

            if not found_files:
                logging.debug("No se encontraron archivos con extensiones compatibles.")
                return jsonify({"error": "No se encontraron archivos compatibles xd"}), 400
            
            return jsonify({"metrics": results})

    except Exception as e:
        logging.error(f"Error al procesar el repositorio: {str(e)}")
        return jsonify({"error": "Error al procesar el repositorio", "details": str(e)}), 500

if __name__ == '__main__':
    app.run()

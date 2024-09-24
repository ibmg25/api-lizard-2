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
        repo_api_url = repo_url.replace('https://github.com/', 'https://api.github.com/repos/')
        repo_info = requests.get(repo_api_url).json()
        default_branch = repo_info.get('default_branch', 'main')
        
        download_url = f"{repo_url}/archive/refs/heads/{default_branch}.zip"

        response = requests.get(download_url)
        if response.status_code != 200:
            return jsonify({"error": "Error al descargar el repositorio"}), 500
        
        with tempfile.TemporaryDirectory() as tmpdirname:
            zip_path = os.path.join(tmpdirname, 'repo.zip')
            with open(zip_path, 'wb') as zip_file:
                zip_file.write(response.content)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdirname)

            extracted_dir = os.path.join(tmpdirname, os.listdir(tmpdirname)[0])
            supported_extensions = ['.rb', '.py', '.js', '.cpp', '.java']  

            results = []
            for root, _, files in os.walk(extracted_dir):
                for file in files:
                    if any(file.endswith(ext) for ext in supported_extensions):
                        file_path = os.path.join(root, file)
                        try:
                            analysis = lizard.analyze_file(file_path)
                            if not analysis.function_list:
                                continue  
                            for func in analysis.function_list:
                                results.append({
                                    "file": file_path,
                                    "function_name": func.name,
                                    "nloc": func.nloc,
                                    "cyclomatic_complexity": func.cyclomatic_complexity,
                                    "token_count": func.token_count,
                                })
                        except Exception as e:
                            print(f"Error analizando {file_path}: {e}")

            return jsonify({"metrics": results})

    except Exception as e:
        return jsonify({"error": "Error al procesar el repositorio", "details": str(e)}), 500

if __name__ == '__main__':
    app.run()

import lizard

file_path = 'C:/Cato/7mo_Semestre/Tecnologías_Web/api-tiendita/src/controllers/orderDetails.controller.js'

analysis = lizard.analyze_file(file_path)

print(f"Análisis de {file_path}:")
for func in analysis.function_list:
    print(f"Función: {func.name}")
    print(f"  Líneas de código (NLOC): {func.nloc}")
    print(f"  Complejidad ciclomática: {func.cyclomatic_complexity}")
    print("------")
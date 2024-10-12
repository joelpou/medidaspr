import time
from enum import Enum
import ollama

class MeasureCategory(Enum):
    ECONOMIC = "Económico"
    SECURITY_DEFENSE = "Seguridad y Defensa"
    HEALTH_WELFARE = "Salud y Bienestar"
    EDUCATION_CULTURE = "Educación y Cultura"
    ENVIRONMENT_ENERGY = "Medio Ambiente y Energía"
    JUSTICE_HUMAN_RIGHTS = "Justicia y Derechos Humanos"
    TECHNOLOGY_INNOVATION = "Tecnología e Innovación"
    FOREIGN_RELATIONS = "Relaciones Exteriores"
    OTHERS = "Otros"

category_values = [member.value for member in MeasureCategory]


start = time.time()
# measure = 'Para añadir un nuevo párrafo al Artículo II, se añaden los nuevos incisos (ii) ,(jj), (kk), (ll), (mm) y (nn) al Artículo III, \
#   añadir un nuevo inciso (s) la Sección II del Artículo IV y añadir un nuevo Artículo X a la Ley Núm. 72 - 1993 según enmendada, mejor \
#   conocida como la “Administración de Seguros de Salud de Puerto Rico” a los fines de ser el pagador único directo de los servicios \
#   médicos provistos por la Administración de Servicios Médicos de Puerto Rico (ASEM), el Centro Cardiovascular de Puerto Rico y del \
#   Caribe (CCCPRC), el Hospital Pediátrico Universitario Dr. Antonio Ortiz (HOPU), el Hospital Universitario de Adultos (UDH), el \
#   Hospital Universitario Dr. Ramón Ruiz Arnau de Bayamón (HURRA) y al Cuerpo de Emergencias Médicas de Puerto Rico (CEMPR) a los \
#   beneficiarios de la Reforma de Salud, establecer los requisitos; y para otros fines.'

measure = '''Para establecer como política pública del Estado Libre Asociado de Puerto Rico la erradicación del hambre y fomentar e 
  incentivar el manejo eficaz de excedentes de alimentos, a fin de promover una mayor y mejor distribución y suplido de alimentos; 
  asegurar la integración y consideración de los aspectos legales en los esfuerzos gubernamentales por atender las necesidades sociales 
  y alimentarias de nuestra población, entre otras; promover la evaluación de otras políticas, programas y gestiones gubernamentales que 
  puedan estar confligiendo o impidiendo el logro de los objetivos de esta Ley; crear el Programa de Organizaciones No Gubernamentales
  adscrito al Departamento de Estado, la Comisión para la Planificación de Distribución de Excedentes de Alimentos adscrita a dicho 
  programa; y establecer sus deberes y responsabilidades.'''

response = ollama.chat(model='llama3.1:8b', messages=[
  {
    'role': 'system',
    'content': f'''
     Eres un experto en la legislación de Puerto Rico y tu objetivo es enseñar a los adolescentes sobre las diversas \
     medidas que se debaten y analizan dentro de esta rama del gobierno de una forma básica. Explica concisamente y brevemente.
     La respuesta sera solamente un JSON con la siguiente estructura:
     
     {{
        "summary": "Resumen del propósito de la medida legislativa en una oración.",
        "category": "Decide a que categoría pertenece esta medida de acuerdo a {category_values}"
      }}
    '''
  },
  {
    'role': 'user',
    'content': f'Resume la siguiente medida usando la estructura JSON establecida: {measure}.',
  }
])

end = time.time()
total_time = end - start
print("Elapsed time: "+ str(round(total_time, 2)) + " seconds")
print(response['message']['content'])
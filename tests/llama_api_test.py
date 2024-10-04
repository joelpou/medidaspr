import os
from typing import Dict, List
from groq import Groq

# Get a free API key from https://console.groq.com/keys
os.environ["GROQ_API_KEY"] = "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"

# LLAMA3_405B_INSTRUCT = "llama-3.1-405b-reasoning" # Note: Groq currently only gives access here to paying customers for 405B model
LLAMA3_70B_INSTRUCT = "llama-3.1-70b-versatile"
# LLAMA3_8B_INSTRUCT = "llama3.1-8b-instant"

DEFAULT_MODEL = LLAMA3_70B_INSTRUCT

client = Groq()

def assistant(content: str):
    return { "role": "assistant", "content": content }

def user(content: str):
    return { "role": "user", "content": content }

def chat_completion(
    messages: List[Dict],
    model = DEFAULT_MODEL,
    temperature: float = 0.6,
    top_p: float = 0.9,
) -> str:
    response = client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=temperature,
        top_p=top_p,
    )
    return response.choices[0].message.content
        

def completion(
    prompt: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.6,
    top_p: float = 0.9,
) -> str:
    return chat_completion(
        [user(prompt)],
        model=model,
        temperature=temperature,
        top_p=top_p,
    )

def complete_and_print(prompt: str, model: str = DEFAULT_MODEL):
    print(f'==============\n{prompt}\n==============')
    response = completion(prompt, model)
    print(response, end='\n\n')
    
if __name__ == '__main__':
    measure_title = 'Para crear el Plan Integral de Salud del Estado Libre Asociado de Puerto Rico para que cubra a todos los puertorriqueños que sean residentes bona fide del país; establecer la nueva política pública de salud en Puerto Rico; crear la Administración Central del Plan Integral de Salud de Puerto Rico, corporación pública que pondrá en vigor y administrará el Plan Integral de Salud de Puerto Rico; definir sus poderes, deberes y funciones bajo los principios de integralidad, equidad, accesibilidad, responsabilidad ciudadana, libre selección, distribución de recursos, regionalización, eficiencia, educación y prevención; establecer los beneficios y servicios de salud física y mental a la ciudadanía puertorriqueña; establecer la Junta de Farmacología, sus poderes, funciones y deberes; disponer sobre las drogas y medicamentos, precio, despacho de recetas y la sustitución de éstos; disponer sobre las facilidades de salud participantes y la contratación de profesionales; establecer el Fondo del Plan Integral de Salud de Puerto Rico, las primas y contribuciones, sobre las cuentas del Plan Integral de Salud de Puerto Rico; disponer sobre las contrataciones y contratos de seguro; establecer sobre reclamaciones de daños y perjuicios; autorizar a dicha Corporación a desarrollar, construir, ampliar, mejorar, arrendar y conservar proyectos para el establecimiento de facilidades de salud; proveer para el financiamiento y refinanciamiento de tales proyectos mediante la emisión de bonos pagarés por dicha Corporación, establecer la Cuenta Corpus y crear el Fondo de Infraestructura de Salud, disponer sobre el acrecentamiento y usos de los fondos de infraestructura, autorizar los convenios con otras agencias, corporaciones públicas, instrumentalidades y subdivisiones políticas del Gobierno del Estado Libre Asociado de Puerto Rico, sobre las facilidades de salud; conferir poderes a otras agencias y subdivisiones políticas del Estado Libre Asociado de Puerto Rico en relación con dichos proyectos; y para otros fines.'
    complete_and_print(f"Tengo esta medida legislativa: {measure_title} \
        En que categoria de medidas legislativas colocarias esta medida? Tambien explicala como para que un nino la entienda.")

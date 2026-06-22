# **Optimización de Documentación de Software para Modelos de Lenguaje (LLM-Friendly): Manual de Ingeniería para Entornos Python y TypeScript**

## **Paradigmas Técnicos de la Documentación Orientada a Agentes de Inteligencia Artificial**

La transición desde la documentación de software concebida exclusivamente para humanos hacia interfaces de conocimiento legibles por máquinas representa un cambio metodológico profundo en la ingeniería de software moderna.1 Tradicionalmente, los manuales técnicos se estructuraban asumiendo la capacidad del lector humano para realizar lecturas no lineales, ignorar elementos visuales superfluos y resolver ambigüedades interpretativas a través del contexto operativo implícito.2 Sin embargo, los modelos de lenguaje de gran escala (LLM) y los agentes autónomos de programación leen la información de manera estrictamente lineal, buscando coincidencias estructurales exactas, restricciones de tipos explícitas y patrones sintácticos de alta fidelidad.3 Cuando un agente de inteligencia artificial es forzado a ingerir documentación renderizada en formatos HTML estándar, se ve obligado a procesar un volumen masivo de código CSS, scripts de seguimiento de JavaScript y estructuras de navegación redundantes, lo que no solo degrada el rendimiento del modelo debido al ruido del contexto, sino que además agota rápidamente su ventana de tokens disponibles.1  
Este escenario ha impulsado la aparición de la Optimización para Motores Generativos (GEO) y la Optimización para Motores de Respuesta (AEO) dentro de la arquitectura de la información técnica.1 En este nuevo ecosistema, la viabilidad y adopción de una biblioteca de código o una API ya no dependen únicamente de su posicionamiento en motores de búsqueda tradicionales, sino de la facilidad con la que asistentes de programación como Cursor, Claude Code, Copilot y Windsurf pueden asimilar, indexar y aplicar sus funciones en tiempo real.1 La entrega de documentación optimizada estructuralmente para LLMs garantiza que el código sugerido por estos asistentes virtuales respete de forma consistente las convenciones de diseño del proyecto, disminuya los errores de sintaxis y mitigue las alucinaciones vinculadas a APIs obsoletas.6  
La introducción de guías de desarrollo optimizadas y la simplificación de procesos mediante estándares de documentación dedicados han demostrado un impacto directo en la eficiencia operativa de los equipos de desarrollo. Diversas implementaciones de flujos documentales optimizados han registrado métricas de rendimiento sobresalientes:

| Métrica de Rendimiento Evaluada | Impacto Cuantitativo Observado | Implicación Operativa |
| :---- | :---- | :---- |
| Tiempo de Onboarding de Desarrolladores | Reducción del 38% 10 | Integración acelerada de nuevos ingenieros a la base de código. |
| Solicitudes de Aclaración Interna | Reducción del 52% 10 | Menor fricción comunicativa y mayor autonomía del equipo. |
| Tiempo de Inicialización de Contexto de IA | Reducción a menos de 5 segundos 11 | Minimiza el retraso en la carga de directivas en sesiones de agente. |
| Errores de Corrección Manual | Reducción del 40% en proyectos TS 11 | Generación de código alineada con las convenciones de diseño. |

## **Especificación y Arquitectura del Estándar llms.txt y sus Variantes de Escala**

El estándar llms.txt, propuesto por el investigador de inteligencia artificial Jeremy Howard y desarrollado en conjunto con el equipo de Answer.ai en septiembre de 2024, define un archivo de texto plano con formato Markdown localizado en la raíz de un dominio web o repositorio (por ejemplo, example.com/llms.txt), cuyo propósito exclusivo es actuar como índice y carta de presentación para rastreadores de IA y agentes de desarrollo.1 A diferencia de los archivos robots.txt, diseñados para restringir el acceso de los rastreadores automatizados, el archivo llms.txt actúa como un mapa de carreteras semántico que orienta a los modelos hacia recursos limpios y canonicalizados.1  
De acuerdo con la especificación técnica oficial establecida en llmstxt.org, el archivo de índice debe respetar de manera estricta la siguiente jerarquía estructural y de ordenación en Markdown 12:

1. **Título de Proyecto (H1):** Declara de forma obligatoria y unívoca el nombre de la biblioteca, producto o base de código.15  
2. **Resumen Ejecutivo (Bloque de Cita \>):** Define de manera concisa el propósito del software. Funciona técnicamente como una instrucción de sistema de alto nivel para contextualizar al modelo sobre el dominio operativo del código.15  
3. **Sección de Directivas Generales:** Párrafos descriptivos o listas no jerárquicas situados inmediatamente debajo del resumen ejecutivo, dedicados a explicar guías globales de interpretación del proyecto sin el uso de encabezados de sección.12  
4. **Secciones de Enlaces (H2):** Agrupaciones temáticas delimitadas por encabezados de segundo nivel que contienen listas de elementos Markdown estructurados mediante la sintaxis de enlace requerida (URL). Opcionalmente, se puede añadir un signo de dos puntos (:) seguido de notas explicativas y descripciones sintéticas para que el LLM decida de antemano si necesita consumir la URL completa.12  
5. **Sección de Contenido Opcional (H2 con nombre "Optional"):** Encabezado con semántica especial integrada en el estándar. Indica de manera explícita que las URL anidadas en esta sección aportan información secundaria y pueden omitirse por completo si la ventana de contexto del modelo de lenguaje es muy restrictiva.12

Para resolver las limitaciones de procesamiento asociadas a la escala de la base de código y evitar la sobrecarga cognitiva del modelo, el ecosistema técnico implementa un enfoque de distribución jerárquica de la documentación.1 Las organizaciones han adoptado diferentes perfiles de tokens y segmentaciones modulares en función de la complejidad de sus sistemas.5  
La siguiente tabla resume y contrasta la arquitectura de indexación de múltiples organizaciones de referencia en la industria:

| Proyecto / Organización | Archivo de Índice | Volumen en Tokens | Enfoque de Segmentación Arquitectónica |
| :---- | :---- | :---- | :---- |
| **Anthropic** | llms.txt 7 llms-full.txt 7 | 8,364 tokens 7 481,349 tokens 7 | Consolida la totalidad de la API técnica en un único archivo plano mapeado dinámicamente.7 |
| **ZenML** | llms.txt 5 component-guide.txt 5 how-to-guides.txt 5 llms-full.txt 5 | \~120,000 tokens 5 180,000 tokens 5 75,000 tokens 5 600,000 tokens 5 | Divide la documentación en archivos temáticos especializados según el tipo de consulta del desarrollador.5 |
| **Svelte** | llms.txt 17 llms-medium.txt 17 llms-small.txt 17 llms-full.txt 17 | Variables de escala 17 | Implementa versiones comprimidas de la documentación en función de la capacidad de la ventana de contexto de la IA.17 |
| **Modular (MAX / Mojo)** | llms.txt 18 llms-python.txt 18 llms-kernels.txt 18 llms-glossary.txt 18 | Variables por API 18 | Segmenta el índice global en subarchivos específicos por lenguaje y API (Python, C, Kernels, etc.).18 |
| **Skeleton** | llms.txt 19 llms-react.txt 19 llms-svelte.txt 19 llms-full.txt 19 | Variables por framework 19 | Proporciona manuales de referencia optimizados según el entorno técnico del usuario (React vs Svelte).19 |

Además del direccionamiento estático por URL, las herramientas modernas de alojamiento de documentación, como GitBook y Mintlify, exponen servidores de protocolo MCP (Model Context Protocol) en rutas reservadas (por ejemplo, /\~gitbook/mcp), permitiendo que editores de código e inteligencias artificiales locales consulten y exploren de manera programática la estructura interna de los documentos sin necesidad de realizar Web Scraping destructivo sobre las páginas públicas.6

## **Principios de Redacción y Diseño de Reglas para Asistentes de IA**

Escribir manuales de software y archivos de instrucciones de desarrollo para inteligencias artificiales requiere desaprender ciertas prácticas típicas de la redacción técnica dirigida a humanos.3 Mientras que las personas necesitan explicaciones analógicas, marcos conceptuales profundos e introducciones narrativas detalladas, los LLM operan de manera más eficiente con instrucciones técnicas que se centren directamente en la aplicación práctica y la gestión de la sintaxis.21 Esto se debe a que los modelos ya han asimilado la mayor parte de la teoría de la programación global gracias a sus conjuntos de datos de entrenamiento; en consecuencia, solo necesitan indicaciones concretas que les permitan usar una interfaz específica sin cometer errores sintácticos.21  
Para estructurar directivas lógicas robustas que los asistentes de programación no pasen por alto, se deben aplicar los siguientes principios de diseño instruccional 21:

* **Granularidad Específica por Entorno:** Evitar la creación de un único archivo masivo de reglas generales que mezcle múltiples lenguajes de programación o entornos técnicos.21 Es preferible dividir las directivas en archivos independientes especializados por lenguaje o dominio.21 Esta separación evita que un modelo que está generando código en TypeScript reciba instrucciones innecesarias de Python, reduciendo la carga cognitiva del prompt.21  
* **Enfoque de Redacción Directa (Cómo vs Qué):** Omitir explicaciones históricas detalladas o justificaciones conceptuales sobre por qué se implementó una función.21 En su lugar, proporcionar descripciones claras sobre el comportamiento de la interfaz y las circunstancias técnicas en las que debe ser utilizada en el código.21  
* **Foco en el Registro de Opciones en Ejemplos:** En lugar de documentar cada propiedad o argumento de configuración mediante largas listas de viñetas descriptivas, integrar las variables directamente como comentarios aclaratorios dentro de ejemplos prácticos de código.21 Los modelos asimilan con mayor naturalidad los parámetros cuando los ven en contexto de ejecución.21  
* **Alineación Semántica Positiva:** Estructurar las pautas metodológicas utilizando patrones afirmativos de buenas prácticas en lugar de prohibiciones.21 Debido a la naturaleza probabilística de los LLM, las directivas redactadas de forma negativa ("No utilices X") pueden generar un efecto de cebado (priming), incrementando la probabilidad de que el modelo use precisamente el patrón prohibido.21 Las prohibiciones explícitas ("DO NOT") deben reservarse como último recurso técnico únicamente para alertar sobre incompatibilidades críticas de versiones o cambios de diseño importantes.9  
* **Instrucciones Basadas en la Periferia del Contexto:** Dado que los modelos de lenguaje tienden a prestar mayor atención a las instrucciones ubicadas al inicio y al final de los prompts (efecto de primacía y recencia), las reglas de mayor prioridad deben declararse en los márgenes de los archivos documentales.22  
* **Evitar el Exceso de Ejemplos de Pocos Pasos (Few-shot Overfitting):** Proporcionar únicamente uno o dos ejemplos representativos completos y de gran calidad que ilustren la arquitectura deseada.21 Añadir múltiples variaciones del mismo patrón de código puede provocar que el modelo se sobreajuste a los datos del ejemplo y pierda flexibilidad al generar soluciones en escenarios distintos.21

## **Implementación Práctica en Python: Modelos Pydantic, Docstrings y Automatización**

Para que un asistente de desarrollo en Python opere de manera determinista, es indispensable que la base de código elimine la ambigüedad dinámica característica del lenguaje.23 Esto se logra implementando tipado estático estricto compatible con herramientas de análisis (PEP 484\) y validadores de datos en tiempo de ejecución basados en Pydantic.23 Al estructurar los modelos con Pydantic, la firma de una función o herramienta deja de ser una declaración semántica vaga para convertirse en un esquema estricto (JSON Schema), lo que permite que el LLM procese y devuelva respuestas estructuradas sin riesgo de errores de tipado.23  
La documentación interna del código debe seguir de manera estricta el estilo de docstrings de Google.24 Este estándar facilita el análisis estático mediante herramientas automatizadas y permite que los modelos extraigan descripciones de parámetros directamente para su uso en la declaración de herramientas (Function Calling).26  
La relación entre la carga semántica de los archivos de documentación y la ventana de contexto disponible del modelo de lenguaje puede modelarse matemáticamente para comprender el impacto del exceso de texto en la inferencia del asistente. El presupuesto de contexto operativo disponible para la computación y generación de respuestas de código se define mediante la siguiente inecuación lineal:  
![][image1]  
Donde ![][image2] representa el límite máximo de tokens soportado por la ventana de contexto de la IA; ![][image3] corresponde a la carga fija de tokens consumida por las instrucciones base del asistente y directivas de entorno; ![][image4] representa el tamaño en tokens de cada archivo de la base de código cargado de forma activa en la conversación; ![][image5] representa el peso del historial acumulado del chat interactivo; y ![][image6] constituye el margen de tokens remanente reservado exclusivamente para la generación de la respuesta analítica de programación.11 Esta relación matemática demuestra por qué documentar el código de forma concisa y sin redundancias narrativas es esencial para maximizar la capacidad de generación y prevenir la pérdida de atención del modelo.11  
En el ecosistema Python, la automatización del pipeline de documentación se realiza integrando el generador estático MkDocs junto con el complemento mkdocstrings (para parsear dinámicamente las firmas del código) y el plugin especializado mkdocs-llmstxt.28 Esta arquitectura garantiza que cualquier cambio estructural en el código fuente actualice instantáneamente el archivo /llms.txt expuesto de forma pública.28  
A continuación se detalla la configuración recomendada para el archivo mkdocs.yml utilizando el complemento de automatización 29:

YAML  
site\_name: "API de Procesamiento de Datos de Alta Precisión"  
site\_url: "https://api.docs.internal/"  
theme:  
  name: "material"

plugins:  
  \- search  
  \- mkdocstrings:  
      default\_handler: python  
  \- llmstxt:  
      markdown\_description: \>  
        Librería de alto rendimiento para el análisis sintáctico de datos estructurados.  
        Garantiza validaciones deterministas e interfaces preparadas para agentes de IA  
        mediante modelos tipados de Pydantic y firma de contratos de API estrictos.  
      sections:  
        Introducción:  
          \- index.md: Guía general y conceptos de arquitectura base  
          \- instalacion.md: Proceso de instalación y configuración de dependencias  
        Estructura de Datos:  
          \- esquemas/\*.md

El siguiente ejemplo de producción en Python ilustra la aplicación práctica de tipado estricto, modelos de validación Pydantic, documentación a nivel de módulo y docstrings con formato de Google, incluyendo excepciones y casos de prueba doctest:

Python  
"""Módulo de procesamiento y cálculo financiero para transacciones internacionales.

Este módulo expone los esquemas de validación deterministas y las operaciones de  
conversión de divisa, diseñados para garantizar la consistencia aritmética de  
los datos y la fácil interpretación de esquemas por parte de agentes de IA.  
"""

from decimal import Decimal, ROUND\_HALF\_UP  
from typing import Dict, Any  
from pydantic import BaseModel, Field, field\_validator

class TransaccionFinanciera(BaseModel):  
    """Modelo de datos estricto para transacciones monetarias estructuradas.

    Define las restricciones de entrada de datos financieros mediante la  
    asociación de tipos fuertes y reglas de validación de negocio complejas.  
    """

    identificador: str \= Field(  
       ...,   
        description="Identificador único global en formato alfanumérico estricto."  
    )  
    monto: Decimal \= Field(  
       ...,   
        description="Valor monetario neto asociado a la transacción comercial."  
    )  
    divisa: str \= Field(  
       ...,   
        description="Código ISO 4217 de tres caracteres para la moneda de origen."  
    )

    @field\_validator("monto")  
    @classmethod  
    def validar\_monto\_positivo(cls, valor: Decimal) \-\> Decimal:  
        """Garantiza que el monto de la transacción sea estrictamente positivo.

        Args:  
            valor: Instancia de Decimal que representa la entrada cruda.

        Returns:  
            Instancia de Decimal que cumple la validación positiva de negocio.

        Raises:  
            ValueError: Si el valor de entrada es menor o igual a cero.  
        """  
        if valor \<= Decimal("0.00"):  
            raise ValueError("El monto financiero debe ser estrictamente superior a cero.")  
        return valor

def calcular\_cambio\_divisa(  
    transaccion: TransaccionFinanciera,   
    tasa\_cambio: Decimal  
) \-\> Decimal:  
    """Calcula el cambio de divisa aplicando un factor aritmético preciso.

    Aplica un redondeo estándar de tipo simétrico (ROUND\_HALF\_UP) para mitigar  
    errores de precisión en operaciones de punto flotante sobre transacciones.

    Args:  
        transaccion: Instancia validada de TransaccionFinanciera.  
        tasa\_cambio: Valor de conversión directa para la moneda destino.

    Returns:  
        Decimal que representa el monto convertido y debidamente redondeado.

    Raises:  
        ValueError: Si la tasa de cambio proporcionada es inválida o negativa.

    Example:  
        \>\>\> trans \= TransaccionFinanciera(  
       ...     identificador="TX-100",   
       ...     monto=Decimal("100.00"),   
       ...     divisa="USD"  
       ... )  
        \>\>\> calcular\_cambio\_divisa(trans, Decimal("0.92"))  
        Decimal('92.00')  
    """  
    if tasa\_cambio \<= Decimal("0.0000"):  
        raise ValueError("La tasa de conversión de divisas debe ser estrictamente positiva.")  
      
    monto\_convertido \= transaccion.monto \* tasa\_cambio  
    return monto\_convertido.quantize(Decimal("0.01"), rounding=ROUND\_HALF\_UP)

## **Implementación Práctica en TypeScript: Compilador Estricto, TSDoc y Estructuras Polimórficas**

En el entorno de desarrollo de TypeScript, la habilitación de un tipado riguroso es la decisión de diseño de mayor impacto para garantizar la consistencia en el código generado por IA.25 Al configurar el compilador en su nivel de máxima rigurosidad ("strict": true en el archivo tsconfig.json), el sistema de tipos de TypeScript funciona de manera análoga a un sistema de verificación estricto.25 Las inconsistencias lógicas introducidas por el modelo se traducen de inmediato en errores de compilación legibles, permitiendo que el asistente de IA identifique el error semántico de manera unívoca y corrija su propia propuesta en un ciclo cerrado de retroalimentación.32  
Para enriquecer este comportamiento, el código debe incorporar los siguientes patrones técnicos de nivel avanzado:

* **Tipos de Marca Semántica (Branded Types):** Dado que TypeScript cuenta con un sistema de tipos estructural, las variables numéricas o de texto simples con fines de negocio distintos (como el identificador de un usuario frente a un identificador de pedido) pueden asignarse erróneamente de forma cruzada sin alertar al compilador.32 Al inyectar una propiedad única ficticia a nivel de tipo (brand), se fuerza una firma nominal estricta que impide mezclar contextos lógicos y que el modelo de IA asimila inmediatamente.32  
* **Uniones Discriminadas:** Permiten la creación de estructuras de datos polimórficas seguras donde un atributo literal unívoco (por ejemplo, type: "success" | "error") actúa como selector de propiedades lógicas específicas, forzando al LLM a instanciar y validar flujos condicionales de control correctos en tiempo de diseño.25  
* **Sintaxis TSDoc Descriptiva:** Los comentarios estructurados deben utilizar etiquetas precisas orientadas al análisis semántico.33

El análisis del cumplimiento de estas directrices de comentarios en TypeScript se puede automatizar en entornos de CI/CD utilizando herramientas como el linter interno de Deno (deno doc \--lint), el cual evalúa de forma automática la existencia de desviaciones lógicas bajo tres códigos de error clave 33:

| Código de Error del Linter | Naturaleza del Desvío Semántico Identificado | Impacto Técnico en los Agentes de IA |
| :---- | :---- | :---- |
| missing-jsdoc | El símbolo o la función expuesta carece por completo de bloque JSDoc/TSDoc.33 | El modelo no recibe explicaciones conceptuales de los parámetros de llamada de la firma.34 |
| missing-return-type | La función pública carece de una declaración de tipo de retorno explícita.33 | Obliga al modelo a inferir el tipo resultante, elevando el riesgo de desviaciones.31 |
| private-type-ref | El tipo de la interfaz pública hace referencia a tipos internos que no han sido exportados.33 | El asistente genera firmas de tipos inválidas al no poder importar las dependencias requeridas.33 |

El siguiente ejemplo práctico implementa estos patrones avanzados en TypeScript, definiendo marcas de tipo nominales, uniones discriminadas y bloques TSDoc completos:

TypeScript  
/\*\*  
 \* @fileoverview Módulo de facturación y cobro electrónico.  
 \* Define la estructura semántica y las operaciones aritméticas seguras  
 \* para la ejecución de cargos de forma automatizada mediante pasarelas de pago.  
 \*/

/\*\*  
 \* Tipo nominal estricto para representar un Identificador de Usuario validado.  
 \* Previene la asignación accidental de identificadores de distinta naturaleza semántica.  
 \*/  
export type UsuarioID \= string & { readonly \_\_brand: unique symbol };

/\*\*  
 \* Tipo nominal estricto para representar un Identificador de Factura válido.  
 \*/  
export type FacturaID \= string & { readonly \_\_brand: unique symbol };

/\*\*  
 \* Interfaz base para operaciones comerciales exitosas.  
 \*/  
export interface CargoExitoso {  
  readonly tipo: "exito";  
  readonly transaccionId: string;  
  readonly montoProcesado: number;  
}

/\*\*  
 \* Interfaz para representar la traza detallada de un error en el cobro.  
 \*/  
export interface CargoFallido {  
  readonly tipo: "error";  
  readonly codigoError: string;  
  readonly mensajeError: string;  
}

/\*\*  
 \* Unión discriminada para encapsular los resultados posibles del motor de pagos.  
 \*/  
export type ResultadoCargo \= CargoExitoso | CargoFallido;

/\*\*  
 \* Clase contenedora de utilidades de conversión de identificadores crudos.  
 \* Facilita el moldeo seguro de datos de entrada hacia tipos con marcas semánticas.  
 \*/  
export class IdentificadorConvertidor {  
  /\*\*  
   \* Valida y moldea un texto plano hacia el tipo nominal fuerte UsuarioID.  
   \*  
   \* @param identificador \- El identificador crudo proveniente de la entrada.  
   \* @returns El identificador transformado bajo la marca nominal del tipo.  
   \* @throws {TypeError} Si el formato del identificador no cumple la expresión regular requerida.  
   \*  
   \* @example  
   \* \`\`\`ts  
   \* const userId \= IdentificadorConvertidor.comoUsuarioID("usr\_9921");  
   \* \`\`\`  
   \*/  
  public static comoUsuarioID(identificador: string): UsuarioID {  
    if (\!identificador.startsWith("usr\_")) {  
      throw new TypeError("El identificador de usuario debe iniciar con el prefijo 'usr\_'.");  
    }  
    return identificador as UsuarioID;  
  }  
}

/\*\*  
 \* Ejecuta una operación de cobro transaccional sobre un usuario del sistema.  
 \*  
 \* @param usuario \- El identificador nominal estricto del usuario destinatario.  
 \* @param factura \- El identificador nominal de la factura asociada al cobro.  
 \* @param monto \- El monto total a cobrar, expresado en centavos de la moneda base.  
 \* @returns Promesa que resuelve en una unión discriminada del tipo ResultadoCargo.  
 \* @throws {RangeError} Si el monto provisto es menor o igual a cero.  
 \*  
 \* @example  
 \* \`\`\`ts  
 \* const usuario \= IdentificadorConvertidor.comoUsuarioID("usr\_100");  
 \* const factura \= "fac\_5502" as FacturaID;  
 \* const resultado \= await procesarCobro(usuario, factura, 1500);  
 \* if (resultado.tipo \=== "exito") {  
 \*   console.log(resultado.transaccionId);  
 \* }  
 \* \`\`\`  
 \*/  
export async function procesarCobro(  
  usuario: UsuarioID,  
  factura: FacturaID,  
  monto: number  
): Promise\<ResultadoCargo\> {  
  if (monto \<= 0) {  
    throw new RangeError("El monto financiero para el cargo debe ser estrictamente superior a cero.");  
  }

  try {  
    // La implementación real simula una llamada de red segura externa.  
    const transaccionId \= \`tx\_api\_${Date.now()}\`;  
    return {  
      tipo: "exito",  
      transaccionId,  
      montoProcesado: monto,  
    };  
  } catch (error: unknown) {  
    return {  
      tipo: "error",  
      codigoError: "GATEWAY\_TIMEOUT",  
      mensajeError: error instanceof Error? error.message : "Error desconocido.",  
    };  
  }  
}

## **Orquestación de Instrucciones de Agente y Memoria (CLAUDE.md,.cursorrules y MEMORY.md)**

La alineación de las directivas globales del repositorio con las sesiones interactivas de los agentes se realiza mediante archivos de configuración en texto plano que los modelos interpretan como reglas del sistema antes de procesar el código.9 Estos archivos permiten definir los estándares del proyecto y evitan que el asistente tenga que deducir las convenciones de diseño empíricamente durante su ejecución.35  
El ecosistema cuenta con diferentes formatos de archivos de directivas en función de la herramienta de desarrollo empleada 9:

* **CLAUDE.md / AGENTS.md (Para Claude Code CLI):** Es cargado automáticamente al inicio de cada terminal interactiva de Claude Code y se inyecta directamente dentro del mensaje de sistema del asistente en cada ciclo de iteración.11  
* **.cursorrules (Para IDE Cursor):** Define guías lógicas aplicables a toda la sesión del editor.9 Cursor permite complementar este archivo mediante reglas de granularidad fina en la ruta .cursor/rules/\*.mdc, las cuales aplican selectivamente basándose en expresiones glob que evalúan las rutas de los archivos activos en pantalla.9  
* **.windsurfrules (Para IDE Windsurf):** Implementa un formato similar enfocado en TypeScript estricto y el uso de retornos tempranos para limitar la anidación del código.9  
* **.github/copilot-instructions.md (Para GitHub Copilot):** Permite inyectar directivas globales de arquitectura y testing para el modelo de Copilot en todo el repositorio.9

La jerarquía de carga de memoria interna de Claude Code sigue una secuencia lineal estructurada que prioriza las directivas del proyecto sobre las globales 11:

1. **\~/.claude/CLAUDE.md (Nivel de Usuario Local):** Almacena preferencias personales del desarrollador que no se comparten en el repositorio.11  
2. **./CLAUDE.md (Nivel de Raíz del Proyecto):** Define de forma compartida en el control de versiones la arquitectura y convenciones obligatorias del equipo.11  
3. **.claude/rules/\*.md (Nivel de Reglas Modulares):** Instrucciones específicas por dominio técnico.11  
4. **\~/.claude/projects/\<hash\>/memory/MEMORY.md (Auto-Memoria del Asistente):** Archivo generado y actualizado de forma autónoma por la IA para recordar patrones de error recurrentes descubiertos a lo largo de las sesiones de trabajo.11

Dado que la memoria autogenerada (MEMORY.md) se evalúa al final del ciclo de contexto, existe el riesgo de que directivas aprendidas empíricamente por la IA contradigan o anulen las directivas explícitas declaradas por el equipo en el archivo CLAUDE.md de la raíz del proyecto.11 De hecho, los análisis de diagnóstico demuestran que el 62% de las inconsistencias en la aplicación de instrucciones de los asistentes de IA se deben a reglas contradictorias presentes en el archivo MEMORY.md.11 El desarrollador debe evaluar regularmente la consistencia de estas trazas mediante el comando interactivo /memory, lo que permite visualizar la longitud de los archivos cargados y purgar directivas obsoletas.11  
La siguiente tabla resume y contrasta el comportamiento operativo y el direccionamiento técnico de los archivos de configuración:

| Archivo de Directiva | Ruta Canónica del Archivo | Activación del Contexto | Aplicación y Gestión de Limitaciones |
| :---- | :---- | :---- | :---- |
| **.cursorrules** | ./.cursorrules 36 | Sesión de Chat global y compositor.9 | Útil para centralizar la identidad del stack, la estructura de carpetas y los comandos de prueba.36 |
| **.cursorrules modulares** | ./.cursor/rules/\*.mdc 35 | Condicional basada en glob patterns de rutas activas.11 | Minimiza el consumo de tokens y el ruido en el prompt al cargar solo reglas aplicables al archivo activo.11 |
| **CLAUDE.md** | ./CLAUDE.md 11 | Inicialización de sesión CLI.11 | Debe centrarse exclusivamente en tres ejes funcionales críticos: el qué, el por qué y el cómo de la base de código.22 |
| **Reglas Modulares Claude** | ./.claude/rules/\*.md 11 | Condicional por frontmatter YAML en rutas coincidentes.11 | Eleva el cumplimiento de directivas específicas en comparación con el uso de archivos monolíticos largos.11 |
| **MEMORY.md** | \~/.claude/projects/\<hash\>/memory/MEMORY.md 11 | Ingestión automática al final del contexto.11 | Su exceso satura el buffer de tokens de sistema. Se trunca de manera silenciosa al superar las 200 líneas.11 |

A continuación se presentan plantillas de configuración optimizadas para entornos Python y TypeScript que pueden ser incorporadas directamente en los proyectos de desarrollo:

### **Configuración de Referencia para CLAUDE.md**

# **API de Cobro y Facturación Financiera**

Servicio de alto rendimiento para procesamiento transaccional financiero y  
validación determinista de esquemas utilizando Python (Pydantic) y TypeScript.

## **Arquitectura y Flujo de Trabajo**

* El backend de cobros reside en /backend (Python con Pydantic y FastAPI).  
* El frontend y lógica del cliente residen en /frontend (TypeScript con tipado estricto).  
* Los contratos de API se sincronizan estrictamente mediante esquemas JSON de transacciones.

## **Comandos de Compilación y Verificación**

* Iniciar Entorno de Pruebas Python: poetry run pytest  
* Ejecutar Análisis Estático de Tipos Python: poetry run mypy.  
* Ejecutar Formateador de Código Python: ruff check. \--fix && ruff format.  
* Compilar Proyecto TypeScript: npm run build  
* Ejecutar Pruebas Unitarias TypeScript: npm run test  
* Validar Consistencia de Tipos TypeScript: npx tsc \--noEmit

## **Estándares de Diseño y Reglas Imperativas**

* ENFORCE tipado estricto en todos los desarrollos. PROHIBIDO el uso de any o variables no tipadas.  
* USE siempre tipos con marca semántica (Branded Types) para identificadores únicos (UsuarioID, FacturaID).  
* WRITE docstrings únicamente bajo el estilo estricto de Google en componentes Python.  
* DEFINE uniones discriminadas para representar resultados condicionales de negocio.  
* CO-LOCATE todas las pruebas unitarias adyacentes a su archivo de implementación de código.  
* DO NOT incluir llaves de API, credenciales de entorno o secretos de desarrollo en este archivo o en la base de código.

### **Configuración de Referencia para.cursorrules**

# **Guías de Desarrollo e Ingeniería del Repositorio**

## **Identidad del Stack**

* Frontend: TypeScript, Node.js v20 (Utilizar estrictamente Importaciones de Módulos ES).  
* Backend: Python v3.11, Pydantic v2 (Utilizar gestor de dependencias Poetry).  
* Convención de Estilo CSS: Tailwind CSS de forma exclusiva en componentes visuales.

## **Estándares de Codificación**

* Utilizar retornos tempranos (early returns) en todas las funciones para evitar niveles de anidación superiores a tres.  
* Escribir comentarios JSDoc/TSDoc detallados en cada función de exportación pública, declarando de forma explícita @param, @returns y @throws.  
* Implementar aserciones inmutables utilizando variables declaradas mediante readonly o const.

## **Requisitos de Pruebas Unitarias**

* Cobertura mínima esperada de pruebas unitarias del 80% sobre cualquier cambio de código.  
* Implementar casos de prueba enfocados a validar la Happy Path de forma aislada a los flujos de gestión de excepciones y errores de tipo.  
* Utilizar Jest en el entorno frontend y Pytest en el entorno backend.

## **Plan de Acción y Secuencia de Despliegue Inmediato**

La transición de una base de código con documentación tradicional hacia un ecosistema de desarrollo optimizado para modelos de lenguaje requiere la ejecución de una secuencia metodológica estructurada en cuatro fases ordenadas cronológicamente para asegurar la asimilación coherente y automática de la documentación por los agentes de IA:

### **Fase 1: Auditoría estructural y maquetación de la información de base**

* **Conversión a Markdown nativo:** Se debe iniciar un barrido completo sobre todas las páginas y manuales de documentación alojados en repositorios internos para convertirlos a Markdown plano (.md), eliminando marcas de formateo enriquecido HTML o componentes JavaScript dinámicos incompatibles con los parseadores lineales de los LLM.2  
* **Consolidación de jerarquías:** Cada archivo resultante debe estructurarse mediante un encabezado jerárquico inequívoco con marcas lógicas estrictas (\#, \#\#, \#\#\#), evitando por completo la introducción de bloques extensos de texto sin delimitadores claros.2  
* **Estructuración semántica de flujos (SOPs):** Para documentar flujos de trabajo internos, tareas del sistema y procedimientos de despliegue, se deben redactar especificaciones basadas en listas de acciones secuenciales numeradas que utilicen verbos imperativos activos precisos (como *aprobar, verificar, enviar, cargar*) en sustitución de términos descriptivos ambiguos, asociando un criterio objetivo de aceptación para cada fase del proceso.10

### **Fase 2: Automatización y exposición del índice de acceso de la IA**

* **Despliegue del índice de recursos:** El equipo de desarrollo debe implementar y exponer un archivo de índice /llms.txt y su respectiva versión consolidada de datos /llms-full.txt en el dominio de producción del proyecto o biblioteca.1  
* **Configuración del build dinámico:** Es necesario integrar la autogeneración de estos archivos en el ciclo de integración continua (CI/CD).1 En proyectos basados en Python, esto se orquesta mediante el uso de los complementos de MkDocs descritos anteriormente, asegurando que la actualización del manual técnico se sincronice en caliente con cada fusión o cambio de versión en la rama principal de producción.28  
* **Activación de políticas de cabecera:** Configurar el servidor web de documentación para inyectar de forma constante las cabeceras HTTP Link y X-Llms-Txt, permitiendo el descubrimiento automático de la configuración por parte de los rastreadores de asistentes de IA externos.20

### **Fase 3: Restricción y verificación mediante herramientas de análisis estático**

* **Configuración estricta de tipado:** Habilitar el compilador de TypeScript con "strict": true en el archivo de opciones del compilador.25 En Python, se debe integrar Mypy en el pipeline para comprobar la solidez de las anotaciones estáticas en cada validación previa al cómit.24  
* **Integración de herramientas de control de estilo:** Configurar la herramienta Ruff en el ecosistema Python para imponer el uso estricto de docstrings con estilo de Google en todos los módulos, clases y métodos expuestos públicamente.24  
* **Auditoría de comentarios de código:** Para proyectos TypeScript, se debe añadir al pipeline un linter con soporte de validación TSDoc para asegurar que ningún desarrollador introduzca funciones sin sus correspondientes parámetros parametrizados e indicación del tipo de salida de retorno.33

### **Fase 4: Limitación del contorno de asistencia local del repositorio**

* **Implantación de archivos de reglas:** Crear en la raíz del repositorio de trabajo los archivos de personalización local de comportamiento CLAUDE.md y .cursorrules.9  
* **Alineación semántica:** Rellenar la configuración interna de ambos archivos describiendo exactamente los comandos necesarios para construir el proyecto, el modo seguro de ejecutar las pruebas unitarias y las restricciones o prácticas de programación expresamente prohibidas en el proyecto.9  
* **Saneamiento continuo:** El desarrollador o arquitecto a cargo del repositorio debe realizar limpiezas periódicas sobre el archivo de autogestión de memoria de la terminal interactiva utilizando el comando integrado /memory para mitigar la aparición de conflictos de comportamiento que desvíen al asistente de las directrices de ingeniería de la organización.11

#### **Obras citadas**

1. What Is LLMs.txt? The Guide To AI Search & GEO \- Yotpo, fecha de acceso: junio 2, 2026, [https://www.yotpo.com/blog/what-is-llms-txt/](https://www.yotpo.com/blog/what-is-llms-txt/)  
2. LLM-Friendly Documentation: Creating Content That AI Can Understand and Process Effectively \- ARON HACK, fecha de acceso: junio 2, 2026, [https://aronhack.com/llm-friendly-documentation-creating-content-that-ai-can-understand-and-process-effectively/](https://aronhack.com/llm-friendly-documentation-creating-content-that-ai-can-understand-and-process-effectively/)  
3. Optimizing technical documentations for LLMs \- DEV Community, fecha de acceso: junio 2, 2026, [https://dev.to/joshtom/optimizing-technical-documentations-for-llms-4bcd](https://dev.to/joshtom/optimizing-technical-documentations-for-llms-4bcd)  
4. Free LLMs.txt Generator Online \- AI SEO Tool \- LLMrefs, fecha de acceso: junio 2, 2026, [https://llmrefs.com/tools/llms-txt-generator](https://llmrefs.com/tools/llms-txt-generator)  
5. Making ML Documentation AI-Friendly: ZenML's Implementation of llms.txt, fecha de acceso: junio 2, 2026, [https://www.zenml.io/blog/llms-txt](https://www.zenml.io/blog/llms-txt)  
6. LLM-ready docs | GitBook Documentation, fecha de acceso: junio 2, 2026, [https://gitbook.com/docs/ai-and-search/llm-ready-docs](https://gitbook.com/docs/ai-and-search/llm-ready-docs)  
7. The Complete Guide to llms.txt: Should You Care About This AI Standard? \- Publii, fecha de acceso: junio 2, 2026, [https://getpublii.com/blog/llms-txt-complete-guide.html](https://getpublii.com/blog/llms-txt-complete-guide.html)  
8. LLM-friendly documentation \- Prepr docs, fecha de acceso: junio 2, 2026, [https://docs.prepr.io/llm-friendly-docs](https://docs.prepr.io/llm-friendly-docs)  
9. The Complete Guide to AI Coding Rules: .cursorrules, CLAUDE.md ..., fecha de acceso: junio 2, 2026, [https://devtk.ai/en/blog/complete-guide-cursorrules/](https://devtk.ai/en/blog/complete-guide-cursorrules/)  
10. Write SOPs For LLMs: Key Strategies For Success \- SOP Heroes, fecha de acceso: junio 2, 2026, [https://sopheroes.com/structured-for-search-write-sops-for-llms/](https://sopheroes.com/structured-for-search-write-sops-for-llms/)  
11. The CLAUDE.md Memory System \- Deep Dive | SFEIR Institute, fecha de acceso: junio 2, 2026, [https://institute.sfeir.com/en/claude-code/claude-code-memory-system-claude-md/deep-dive/](https://institute.sfeir.com/en/claude-code/claude-code-memory-system-claude-md/deep-dive/)  
12. llms-txt: The /llms.txt file, fecha de acceso: junio 2, 2026, [https://llmstxt.org/](https://llmstxt.org/)  
13. Instructor Adopts llms.txt: Making Documentation AI-Friendly, fecha de acceso: junio 2, 2026, [https://python.useinstructor.com/blog/2025/03/19/instructor-adopts-llms-txt/](https://python.useinstructor.com/blog/2025/03/19/instructor-adopts-llms-txt/)  
14. What is llms.txt? Why it's important and how to create it for your docs \- GitBook, fecha de acceso: junio 2, 2026, [https://www.gitbook.com/blog/what-is-llms-txt](https://www.gitbook.com/blog/what-is-llms-txt)  
15. Python source \- llms-txt, fecha de acceso: junio 2, 2026, [https://llmstxt.org/core.html](https://llmstxt.org/core.html)  
16. What is llms.txt? An optimization strategy for AI and its implementation in Drupal | Metadrop, fecha de acceso: junio 2, 2026, [https://metadrop.net/en/articles/what-llmstxt-optimization-strategy-ai-and-its-implementation-drupal](https://metadrop.net/en/articles/what-llmstxt-optimization-strategy-ai-and-its-implementation-drupal)  
17. Docs for LLMs \- Svelte, fecha de acceso: junio 2, 2026, [https://svelte.dev/docs/llms](https://svelte.dev/docs/llms)  
18. Using AI coding assistants \- Modular Documentation, fecha de acceso: junio 2, 2026, [https://docs.modular.com/max/coding-assistants/](https://docs.modular.com/max/coding-assistants/)  
19. LLMs \- Skeleton.dev, fecha de acceso: junio 2, 2026, [https://www.skeleton.dev/docs/svelte/resources/llms](https://www.skeleton.dev/docs/svelte/resources/llms)  
20. llms.txt \- Mintlify, fecha de acceso: junio 2, 2026, [https://www.mintlify.com/docs/ai/llmstxt](https://www.mintlify.com/docs/ai/llmstxt)  
21. Rules for Rules: Writing Docs for LLMs \- mbleigh.dev, fecha de acceso: junio 2, 2026, [https://mbleigh.dev/posts/rules-for-rules/](https://mbleigh.dev/posts/rules-for-rules/)  
22. Writing a good CLAUDE.md | HumanLayer Blog, fecha de acceso: junio 2, 2026, [https://www.humanlayer.dev/blog/writing-a-good-claude-md](https://www.humanlayer.dev/blog/writing-a-good-claude-md)  
23. Episode \#528 \- Python apps with LLM building blocks, fecha de acceso: junio 2, 2026, [https://talkpython.fm/episodes/show/528/python-apps-with-llm-building-blocks](https://talkpython.fm/episodes/show/528/python-apps-with-llm-building-blocks)  
24. code-quality | Skills Marketplace \- LobeHub, fecha de acceso: junio 2, 2026, [https://lobehub.com/de/skills/eggmasonvalue-llm-plugin-artifacts-code-quality](https://lobehub.com/de/skills/eggmasonvalue-llm-plugin-artifacts-code-quality)  
25. TypeScript Best Practices in Large Codebases \- DEV Community, fecha de acceso: junio 2, 2026, [https://dev.to/srini\_k/typescript-best-practices-in-large-codebases-58kc](https://dev.to/srini_k/typescript-best-practices-in-large-codebases-58kc)  
26. Support per-parameter descriptions in \`FunctionTool\` via \`Annotated\[T, Field(description=...)\]\` · Issue \#4552 · google/adk-python \- GitHub, fecha de acceso: junio 2, 2026, [https://github.com/google/adk-python/issues/4552](https://github.com/google/adk-python/issues/4552)  
27. Authoring Python-Based Tools \- IBM watsonx Orchestrate ADK, fecha de acceso: junio 2, 2026, [https://developer.watson-orchestrate.ibm.com/tools/create\_tool](https://developer.watson-orchestrate.ibm.com/tools/create_tool)  
28. Instructor Now Supports llms.txt, fecha de acceso: junio 2, 2026, [https://python.useinstructor.com/blog/2025/08/29/llms-txt-support/](https://python.useinstructor.com/blog/2025/08/29/llms-txt-support/)  
29. Automating llms.txt Generation with mkdocs-llmstxt Plugin \- Instructor, fecha de acceso: junio 2, 2026, [https://python.useinstructor.com/blog/2025/08/29/mkdocs-llmstxt-plugin-integration/](https://python.useinstructor.com/blog/2025/08/29/mkdocs-llmstxt-plugin-integration/)  
30. Build Your Python Project Documentation With MkDocs \- Real Python, fecha de acceso: junio 2, 2026, [https://realpython.com/python-project-documentation-with-mkdocs/](https://realpython.com/python-project-documentation-with-mkdocs/)  
31. Best Practices for Writing Clean TypeScript Code \- DEV Community, fecha de acceso: junio 2, 2026, [https://dev.to/alisamir/best-practices-for-writing-clean-typescript-code-57hf](https://dev.to/alisamir/best-practices-for-writing-clean-typescript-code-57hf)  
32. Why I Choose TypeScript for LLM‑Based Coding | by Thomas Landgraf | Medium, fecha de acceso: junio 2, 2026, [https://medium.com/@tl\_99311/why-i-choose-typescript-for-llm-based-coding-19cbb19f3fa2](https://medium.com/@tl_99311/why-i-choose-typescript-for-llm-based-coding-19cbb19f3fa2)  
33. Generating documentation with deno doc, fecha de acceso: junio 2, 2026, [https://docs.deno.com/examples/deno\_doc\_tutorial/](https://docs.deno.com/examples/deno_doc_tutorial/)  
34. A Comprehensive Guide to next-mcp-server for AI Engineers \- Skywork, fecha de acceso: junio 2, 2026, [https://skywork.ai/skypage/en/A-Comprehensive-Guide-to-next-mcp-server-for-AI-Engineers/1972137785398759424](https://skywork.ai/skypage/en/A-Comprehensive-Guide-to-next-mcp-server-for-AI-Engineers/1972137785398759424)  
35. Mastering Cursor Rules: A Developer's Guide to Smart AI Integration \- DEV Community, fecha de acceso: junio 2, 2026, [https://dev.to/dpaluy/mastering-cursor-rules-a-developers-guide-to-smart-ai-integration-1k65](https://dev.to/dpaluy/mastering-cursor-rules-a-developers-guide-to-smart-ai-integration-1k65)  
36. A Comprehensive Guide to Using .cursorrules for Optimized AI-assisted Programming, fecha de acceso: junio 2, 2026, [https://cursorrules.org/blog/comprehensive-guide-cursorrules-optimized-ai-programming](https://cursorrules.org/blog/comprehensive-guide-cursorrules-optimized-ai-programming)  
37. Overview \- Claude Code Docs, fecha de acceso: junio 2, 2026, [https://code.claude.com/docs/en/overview](https://code.claude.com/docs/en/overview)

[image1]: <data:image/png;base64,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>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADEAAAAaCAYAAAAe97TpAAABWklEQVR4Xu2WsUoDQRCGBwK2vkYaC0lrY5XKIo0PkDdIwNIyldjmAcSQXuxMEQIiImIbQgQbQUklViISZ9xdHP7s7SaegbuwH/ww/z93m527XHJEicRauFpCfdaxO6FoDFlzyMRjJviyQuDbWOmGOMOAsof4xKAI9DBgOmQGaGCDOcKgqGTdhVKxMUN8YMi0yD+cL4txgsF/0iWzqX1sWHDDb6w6ZMsg6xwoX1V1bmJfJextgf8rEwzysMoQeKzUI9YL61H13HGn1l9b34Y+rvfMurRZReVR5IQBhgocMOSllmG0d0zpdwgB17mjcH8BvBK+q+LALOSl3gXveKDwJsXr9zbs5wIXC3mpd8A77ik+xNrAxUM+NETsTryTeXNwZP1arswhmQ/7Ym2zbq1/sv2Z9XL75bmSWrTHGtv6lXWherWfM4luyDzE+v9J+uesJpXodSeRSCQ2iG/UcYOJxUgf4wAAAABJRU5ErkJggg==>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEEAAAAaCAYAAADovjFxAAABuklEQVR4Xu2XsStFcRTHj5SibAaTwU7IYLCwWBj4EwxKNi+LSTKRKIVkFDsjm9hkIoVSBoVBmTBwTvcc9/i+271XevXc9/vUt3vO9/zuz+937n2/9xAFAoEUPhM0nlEvJFmbk1obmkUjrQnPaBSVpCaMJHiFZZuizfY575o15/LCg28B5jWBbbrZxTXbhGPNJzV/+B6RjyU0/hOy4aEE77dvg4yXwzSNCTSqAXvqiByM4pew8Efe0agG0p54Vm1Br8KJxtOat7LeWGtujM2H88q30oF69erZmGHWqcbeX9ZcmGdtUvTx3XB+bmRCWUASuFhjkdWAJnNDcRP8fR8uxvnqwEuL7yA3cP4ml6diG/TyYM3XbeEieQrGOcVNWKXy+wTMb1mvrEOVr2PcA7lHHoq9mR1Qqyiz9HMxZxQ3wdil8s0I8nVs+b3GCN7nN+dr8rFrd36Xq1WMPchH9erfBL/IRxebb79OW5wnDLg4bxMw7mZdOK8iSBPkj8nhd6TevnqiXr3KQho1Nl5YK+BtsXYo+vd9Rr0nisZcsgY1FvWzrjS25sqZ0MlaZ01RdHaMaS0QCAQCgUB+vgAF/qYiy/ZRkgAAAABJRU5ErkJggg==>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAAaCAYAAABVX2cEAAAAkklEQVR4XmNgGLHgP5GYaIBPgxADbjmsAJ9hIIBPDgOAFO9DF0QCJBvGgyb2AYlNtGHVDJiKNwKxE5oYUQA91giFH14A0ngKic8FFcMGVNAF0AFIoyAWMXRwmAHifZygiwG7RrIAseGzioEIdcQaxsSARx16zBFjKCF5kkAhugC54CWUporr3gBxOrrgKBgFOAAACKQ3bUi6k8sAAAAASUVORK5CYII=>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEIAAAAaCAYAAAADiYpyAAAB2ElEQVR4Xu2WzysFURTHjw1ZyK8oK8VCJBb+ATuJhbK0w9IfoFCShWxYYeUfECVLSzZkIxaS8layohSFBfc05zRnvm/uM3hvM+9+6ts953vuvDv3zLz7HlEgEMjIVwk9mXlVgW48Dfbv0MwrPzXCV8sdvNEHNIWqacQqRRvtxYLAtU8080ipJ35J/lru0EYMG80bv2pIawRL0fqs8SwdTo1olpkxSt6Tj389PL5wBE2gQP5G7Dmtown4zp+sfDi9o+nhT42YoGwXFsjfiCzcolFBsuyniKyv0rXTDEVz35wuTI29fYlrJF+TUetWFs43nJYlHxKPf6XsfLyW4x2nR6dt42vt1/BFJ2imcEXFN2I5kBF9Jc233q7TksQtpqZjt4mtr3Ed5JnRDlt1JmYk4TfCngO4mDZikuLPs+cOzl8Ejw9bzRugxrSneLUU/wfqMz7OKys3Tismx8W0EcoWRXPGJcf5h+A1mTytEa3gcdxl4n6oVYx7irqv4GK+r8aZjOgz1uO37VniZqgxbcbbNDHD8SDkFeGYog9nLVC0OY750GReJJ+WkfN6GZVzpyNK/gROOb06jVL8F76H4rV4XQU9jgcoOijnKHpQjN7LqeSBQCAQCATKxzcdDaiNzvB8MAAAAABJRU5ErkJggg==>

[image6]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAE8AAAAaCAYAAAD2dwHCAAACMElEQVR4Xu2YwUsUcRTHXyAIoafAg4cgURAKwYvnCkT/BCW1QweR9Cp4SYigQ4mnvAge1JsE4VWlU0p0KIUuBSlRhOFBkAqCqPd1fo99+2V3dmbVZc3fB77s+743v9/MvJ3fzM6KRCKR/4h51V/SZqj9sY0ixVij2rgQsHqEmJPKjUF9iZMXnWZJGtPJBeIDJyLZl+MaJy46vZK9eRHCGjfIhUhlTnrVlWr+YxfXiicuTjuntFpusk7WpWrlZOCbFDcvy3ynDfbZR74cabVcZG1e2jafpf6WfdrxptVy8UiSya5zwfFWdYlye6qPkozdVQ2EPH8ZiJ+pfqkOXG4lfP4On5511RblbV4cB+ZC3Bhqr4IfDx7A35PkFwLPX8rPSpVvT3zCnjeqbsph23by1jzzoEk15fLWPPDJxQuqnyF+qpp2NW7gPnljVzXhPJ8Pz2Nsu3hU9dL5zBxKoYkPJLmP8QEYnIcvd8+zOV+4HHhN3saUmvu+i8vd13akuuYhxtVp4nG56FDd5CTBO4AvdeUZw6ojymNZetKaN+PiW1Qz3knl5l1zsc/XFOywgfwd8uCGy4FyzRuRQu27asjV+ERvkzeqvfJ+uBjwuDMBO2lRLYcYwtLFzR4x/sJC8xD3qCZVD49HJnxRLaruhm088Phb7Kskb0DAlhTUr3of4g3VqqvhJxVAjIZeCfHVkLfjw8PhcsjBj8k5ev3kZRvJAT8wIhmxJ9tzLkQikUik/vgHb2vD+R62sXwAAAAASUVORK5CYII=>
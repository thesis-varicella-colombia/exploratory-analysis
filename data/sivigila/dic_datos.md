

| Columna  | Descripción |
| -------- | ------- |
| CONSECUTIVE |  |
| COD_EVE | Codigo del evento. Código del Evento según CIE X ó Código del Instituto Nacional de Salud. | 
| FEC_NOT | Fecha de notificacion. AAAA-MM-DD (Año-Mes-Día separado por guiones) (Norma ISO 8601,NTC 1034) | 
| COD_DPTO_N | Codigo del departamento de notificacion. Código del Departamento Según registro Divipola fuente DANE. Ejemplo: Nariño = 52 | 
| COD_MUN_N | Codigo del municipio de notificacion. Código DIVIPOLA municipio | 
| Departamento_Notificacion | Departamento notificacion | 
| Municipio_notificacion | Municipio notificacion | 
| SEMANA | Semana. Semana epidemiológica según calendario vigente Rango. 1-53 | 
| ANO | Año. Año correspondiente a la Semana Epidemiológica  | 
| COD_PRE | Código del prestador de servicios de salud. Código asignado en el SGSSS a los prestadores de servicios de salud que se hayan registrado en el “Registro Especial de Prestadores de Servicios de Salud” Ejemplo: 52 001 00001 | 
| COD_SUB | Código de prestador de servicios de salud – subindice. Código asignado en el SGSSS a los prestadores de servicios de salud que indica sede ó territorio. * | 
| SEXO | Sexo. M = Masculino, F = Femenino, I = Indeterminado | 
| EDAD | Edad. 0 = No aplica, Edad en números en enteros del paciente| 
| UNI_MED | Unidad de medida de la edad. 0 = No aplica, 1 = Años, 2 = Meses, 3 = Días, 4 = Horas, 5 = Minutos | 
| estrato | Estrato socioeconomico. 1 = Estrato_1, 2 = Estrato_2, 3 = Estrato_3, 4 = Estrato_4, 5 = Estrato_5, 6 = Estrato_6 | 
| COD_PAIS_O | Codigo del pais de ocurrencia. Código de país internacional |
| COD_DPTO_O | Codigo del departamento de ocurrencia. Código del Departamento Según registro Divipola fuente DANE. Ejemplo: Nariño = 52 | 
| COD_MUN_O | Codigo del municipio de ocurrencia. Código DIVIPOLA municipio | 
| Pais_ocurrencia | Pais de ocurrencia | 
| Nombre_evento | Nombre del evento | 
| Departamento_ocurrencia | Departamento ocurrencia | 
| Municipio_ocurrencia | Municipio ocurrencia | 
| AREA | Area geografica. 1 = Cabecera Municipal 2 =, Centro Poblado 3 = Rural, Disperso | 
| TIP_SS | Tipo de regimen en salud. C = Contributivo, S = Subsidiado, P = Excepción, E = Especial, N = No Asegurado |
| COD_ASE | Código de la entidad responsable de la atención del paciente. Código asignado por el MPS a la Administradora. Si se selecciona la opción 5= no afiliado en la variable tipo de régimen en salud, se desactiva la variable código de administradora. Para las demás opciones es obligatorio su diligenciamiento. | 
| sem_ges | Semana gestante. >=1 AND <=45. (Si GP_GESTAN=1) | 
| PER_ETN | Pertenencia etnica. Es el código asignado por el DANE a la pertenencia étnica, se omiten las etnias consideradas en la clasificación DANE que no tienen evidencia epidemiológica de comportamiento especial para los eventos de interés en salud pública. Se usa la codificación estándar para las de interés: 1 = Indígena, 2 = ROM, Gitano, 3 = Raizal, 4 = Palenquero, 5 = Negro-Mulato-Afro Colombiano, 6 = Otro | 
| GRU_POB | Grupo poblacional | 
| nom_grupo | Nombre del grupo poblacional | 
| GP_DISCAPA | Grupo poblacional - discapacitados. 1 = Sí 2 = No | 
| GP_DESPLAZ | Grupo poblacional - desplazados. 1 = Sí 2 = No | 
| GP_MIGRANT | Grupo poblacional - migrantes. 1 = Sí 2 = No | 
| GP_CARCELA | Grupo poblacional - carcelarios. 1 = Sí 2 = No | 
| GP_GESTAN | Grupo poblacional - gestantes. 1 = Sí 2 = No | 
| GP_INDIGEN | Grupo poblacional - indigentes. 1 = Sí 2 = No | 
| GP_POBICFB | Grupo poblacional - poblacion infantil a cargo del ICBF. 1 = Sí 2 = No | 
| GP_MAD_COM | Grupo poblacional - madres comunitarias. 1 = Sí 2 = No | 
| GP_DESMOVI | Grupo poblacional - desmovilizados. 1 = Sí 2 = No | 
| GP_PSIQUIA | Grupo poblacional - poblacion en centros psiquiatricos. 1 = Sí 2 = No | 
| GP_VIC_VIO | Grupo poblacional - victima de violencia. 1 = Sí 2 = No | 
| GP_OTROS | Grupo poblacional - otros. 1 = Sí 2 = No | 
| COD_PAIS_R | Codigo del pais de residencia | 
| COD_DPTO_R | Codigo del departamento de residencia. Código del Departamento Según registro Divipola fuente DANE. Ejemplo: Nariño = 52 | 
| COD_MUN_R | Codigo del municipio de residencia. Código DIVIPOLA municipio | 
| Pais_residencia | Pais residencia | 
| Departamento_residencia | Departamento residencia | 
| Municipio_residencia | Municipio residencia | 
| FEC_CON | Fecha de constitución o inicio de actividades asistenciales. AAAA-MM-DD (Año-Mes-Día separado por guiones) (Norma ISO 8601,NTC 1034) | 
| INI_SIN | Fecha de inicio de sintomas. AAAA-MM-DD (Año-Mes-Día separado por guiones) (Norma ISO 8601,NTC 1034)  | 
| TIP_CAS | Clasificacion inicial del caso. 1 = Sospechoso, 2 = Probable, 3 = Confirmado por Laboratorio, 4 = Confirmado por Clínica, 5 = Confirmado por Nexo Epidemiológico. |  
| PAC_HOS | Hospitalizado. 1 = Sí 2 = No | 
| FEC_HOS | Fecha de hospitalizacion. AAAA-MM-DD (Año-Mes-Día separado por guiones) (Norma ISO 8601,NTC 1034) | 
| CON_FIN | Condicion final. 0 = No sabe - no responde, 1 = Vivo, 2 = Muerto | 
| FEC_DEF | Fecha de defuncion. AAAA-MM-DD (Año-Mes-Día separado por guiones) (Norma ISO 8601,NTC 1034). (Si CON_FIN=2) | 
| AJUSTE | seguimiento y clasificacion final del caso. 0 = No aplica - No Ajusta - 1ª Vez, 3 = Confirmado por Laboratorio, 4 = Confirmado por Clínica, 5 = Confirmador por Nexo Epidemiológico, 6 = Descartado, 7 = Otro ajuste, D = Descarte por error de digitacion |
| fuente | Fuente. 1 = Notificación rutinaria, 2 = Busqueda Activa Institucional, 3 = Vigilancia intensificada, 4 = Busqueda Activa Comunitaria, 5 = Investigaciones. (Si AJUSTE=0 ó 7) |
| FECHA_NTO | Fecha de nacimiento. AAAA-MM-DD (Año-Mes-Día separado por guiones) (Norma ISO 8601,NTC 1034) | 
| CBMTE | Causa basica de defuncion o muerte. Código de la CIE X (Si CON_FIN=2) |
| FEC_AJU | Fecha de ajuste. Corresponde a la fecha del sistema (systemdate) o a la fecha efectiva de digitación del registro o realizar un ajuste a un registro previo |  
| FM_FUERZA | Fuerza militar. 1 = GAB 2 = CGF 3 = EJC 4 = ARC 5 = FAC 6 = HMC 7 = POL 8 = SIN | 
| FM_UNIDAD | Unidad - codigo de la unidad militar. Código de la Unidad Militar según tabla de Unidades Militares | 
| FM_GRADO | Grado - codigo del grado militar. Código de la Grado Militar según tabla de Grados Militares | 
| confirmados | Confirmados |
| va_sispro | Sistema Integral de Informacion para la Proteccion Social |
| Estado_final_de_caso | Estado final del caso |
| nom_est_f_caso | Nombre de Estado final del caso |
| Nom_upgd | Nombre de la "unidad primaria generadora de dato" que registró el caso | 
| FEC_ARC_XL | Fecha de creacion del archivo de Excel. AAAA-MM-DD (Año-Mes-Día separado por guiones) (Norma ISO 8601,NTC 1034) | 
#!/bin/bash

# direcciones necesarias para saber donde se crean las carpetas y 
#archivo consolidar.sh, uso las {} para forzar la re expansion al verificar #sino no funcionaba y no podia verificar si se creo el directorio

BASE_DIR="${HOME}/EPNro1"
DIR_ENTRADA="${BASE_DIR}/entrada"
DIR_SALIDA="${BASE_DIR}/salida"
DIR_PROCESADO="${BASE_DIR}/procesado"
CONSOLIDAR_SCRIPT="${BASE_DIR}/consolidar.sh"

# Parametro optativo -d
# elimina directorios forzosamente y mata el proceso consolidar.sh

if [[ "$1" == "-d" ]]; then
#busca el proceso con pgrep y manda dev/null para que no se muestre el pid en pantalla 
#pkill se usa como complemento y mata el processo
    if pgrep -f "consolidar.sh" > /dev/null; then
        pkill -f "consolidar.sh"
        echo "Proceso consolidar.sh terminado."
    else
        echo "No habia proceso consolidar.sh activo."
    fi
 #elimina forzoamente con -rf las capeta de epnro1 y todos sus subdirectorios gracias al f
    echo "Eliminando entorno"
    if [[ -d "${BASE_DIR}" ]]; then
        rm -rf "${BASE_DIR}"
        echo "Directorio $BASE_DIR eliminado."
    fi
 
    echo "Entorno eliminado."
    exit 0
fi

#valida que exista la variable de entorno FILENAME
if [[ -z "$FILENAME" ]]; then
    echo "ERROR: La variable de entorno FILENAME no esta definida."
    exit 1
fi
 
# crea el consolidar.sh usando end of file para guardar informacion
# tmb crea las carpetas de entrada, salida, procesado y epnro1
crear_archivos() {
	echo "Creando entorno "
	echo ""
	if [[ -d "${BASE_DIR}" ]]; then
        	echo "El directorio $BASE_DIR ya existe."
        else
        	mkdir -p "$DIR_ENTRADA" "$DIR_SALIDA" "$DIR_PROCESADO"
        	echo "Directorio creado"
        	echo "Subcarpetas creada"
    	fi
#crea el archivo consolidar.sh y envia todo lo de antes de eof a este
    	cat > "${CONSOLIDAR_SCRIPT}" << 'EOF'
#!/bin/bash
while true; do
    for ARCHIVO in "${DIR_ENTRADA}"/*.txt; do
#revisa si existe el archivo para evitar tener que correr el proceso constantemente
        if [[ -f "$ARCHIVO" ]]; then
            NOMBRE=$(basename "$ARCHIVO")
            ARCHIVO_SALIDA="${DIR_SALIDA}/${FILENAME}.txt"
            cat "$ARCHIVO" >> "$ARCHIVO_SALIDA"
            mv "$ARCHIVO" "${DIR_PROCESADO}/${NOMBRE}"
        fi
    done
    sleep 5
done
EOF
 #aplica permisos para que se pueda ejecutar el script
        chmod +x "${CONSOLIDAR_SCRIPT}" 
    
}

correr_proceso() {
    	echo "Iniciando proceso en background"
    	echo "Buscando entorno en: ${BASE_DIR}"
 
    	if [[ ! -d "${BASE_DIR}" ]]; then
        	echo "El entorno no existe. Ejecute primero la opcion 1."
        	return
    	fi
 #exporta las variables para que puedan ser usadas por consolidar.sh
    	export FILENAME
    	export BASE_DIR
    	export DIR_ENTRADA
    	export DIR_SALIDA
    	export DIR_PROCESADO
 #usa nohup para ignorar la senal de kill cuando se cierra la terminal y el disown para que no sea un proceso hijo
 #el  /dev/null 2>&1 redirige la salida a ningún lado para que no moleste
    	nohup bash "${CONSOLIDAR_SCRIPT}" > /dev/null 2>&1 & disown
	echo "Proceso consolidar.sh iniciado en background."
}

listar_alumnos() {
#sort los alumnos usando la primera columna que seria la del padron
	echo "Listando alumnos por padron"
	ARCHIVO_SALIDA="${DIR_SALIDA}/${FILENAME}.txt"
    	sort -k1,1n "${ARCHIVO_SALIDA}"
}

top10_notas() {
#usa sort para la 5ta columna que serian las notas y head para las top 10
   	echo "Top 10 notas mas altas"
    	ARCHIVO_SALIDA="${DIR_SALIDA}/${FILENAME}.txt"
    	sort -k5,5nr "${ARCHIVO_SALIDA}" | head
}

buscar_alumno() {
#utiliza el grep aplicando el RE ^ que seria al principio para busacr por padron, si lo encuentra lo devuelve
	echo "Ingrese el Nro de Padron"
	read PADRON
	
	if [[ -z "$PADRON" ]]; then
        	echo "No ingreso ningun padron."
        	return
    	fi
    	
    	grep "^${PADRON}" "${ARCHIVO_SALIDA}"
}

while true; do
	echo ""
	echo "////////////////////////////////////////"
	echo "                  MENU                      "
	echo "////////////////////////////////////////"
	echo "  1) Crear entorno"
	echo "  2) Correr proceso "
	echo "  3) Listar alumnos por padron"
	echo "  4) Top 10 notas mas altas"
	echo "  5) Buscar alumno por padron"
	echo "  6) Salir"
	echo -n "  Seleccione una opcion [1-6]: "
	echo ""
	    
	read  OPCION
#use un case para que se usen las diferentes opciones y que cada una de estas haga una difernte funcion
	case "$OPCION" in
		1) crear_archivos ;;
		2) correr_proceso ;;
		3) listar_alumnos ;;
		4) top10_notas ;;
		5) buscar_alumno ;;
		6)
		    echo "Saliendo del sistema."
		    exit 0
		    ;;

		*)
		    echo "Opcion invalida. Ingrese un numero entre 1 y 6."
		    ;;
	esac
done




	
	

#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
AUTH_ENDPOINT="${BACKEND_URL}/api/v1/login"
AUTH_USERNAME="admin"     
AUTH_PASSWORD="admin"           
AUTH_TOKEN=""
UPLOAD_ENDPOINT="${BACKEND_URL}/api/v1/documents/upload"
TEST_DIR="./test_pdfs"
LOG_FILE="./init.log"
MAX_RETRIES=3
RETRY_DELAY=5
MAX_FILE_SIZE_MB=20

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PDF_URLS=(
  # Машинное обучение
  "https://zhanibekov.edu.kz/media/university/faculties/materials/%D0%9B%D0%B5%D0%BA%D1%86%D0%B8%D1%8F_1_1.pdf"
  "https://edu.vsu.ru/pluginfile.php/1246728/mod_resource/content/1/191.pdf"
  # Физика (МФТИ, МГУ)
  "https://www.pd.isu.ru/sost/teor_phi/korenb/TDSPh/puhov_lec_sph.pdf"
  "https://chair.itp.ac.ru/biblio/lectures/semiconductors/MIPT_lects.pdf"
  "https://internat.msu.ru/media/uploads/2013/05/%D0%9A%D0%BE%D0%BB-%D1%8F-%D0%B8-%D0%B2%D0%BE%D0%BB%D0%BD%D1%8B-_%D1%87.IV_.pdf"
  # Математика
  "https://books.ifmo.ru/file/pdf/1898.pdf"
  "https://staff.tiiame.uz/storage/users/180/books/jZVbwpKcCCQdJOE3cNPtyyOcsQ3ZVvBxqrZUxgkS.pdf"
  # Java и программирование
  "https://iite.vlsu.ru/fileadmin/faip/uploads/Programming_Java.pdf"
  "https://specialitet.ru/lekcyi/progr/lekcyy_modul_2_vopros_4.pdf"
  # Рефакторинг / разработка ПО
  "https://library.tsilikin.ru/%D0%A2%D0%B5%D1%85%D0%BD%D0%B8%D0%BA%D0%B0/%D0%9F%D1%80%D0%BE%D0%B3%D1%80%D0%B0%D0%BC%D0%BC%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5/Desing/%D0%A0%D0%B5%D1%84%D0%B0%D0%BA%D1%82%D0%BE%D1%80%D0%B8%D0%BD%D0%B3%20%D1%83%D0%BB%D1%83%D1%87%D1%88%D0%B5%D0%BD%D0%B8%D0%B5%20%D0%BF%D1%80%D0%BE%D0%B5%D0%BA%D1%82%D0%B0.pdf"
)

log() {
  local level=$1; shift
  local message="$*"
  local timestamp
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  case $level in
    "INFO")  echo -e "${GREEN}[${timestamp}] [INFO]${NC} $message" | tee -a "$LOG_FILE" ;;
    "WARN")  echo -e "${YELLOW}[${timestamp}] [WARN]${NC} $message" | tee -a "$LOG_FILE" ;;
    "ERROR") echo -e "${RED}[${timestamp}] [ERROR]${NC} $message" | tee -a "$LOG_FILE" ;;
    "STEP")  echo -e "${BLUE}[${timestamp}] [STEP]${NC} $message" | tee -a "$LOG_FILE" ;;
  esac
}

wait_for_api() {
  log "STEP" "Ожидание готовности API на ${BACKEND_URL}..."
  local retries=0
  local max_retries=60
  until curl -sf "${BACKEND_URL}/docs" >/dev/null 2>&1; do
    retries=$((retries + 1))
    if [ $retries -ge $max_retries ]; then
      log "ERROR" "API не готов после $((max_retries * 5)) секунд. Проверьте, запущен ли бэкенд."
      exit 1
    fi
    log "WARN" "API недоступен. Попытка $retries/$max_retries. Повтор через 5 секунд..."
    sleep 5
  done
  log "INFO" "API готов!"
}

get_auth_token() {
  log "STEP" "Получение токена авторизации..."
  
  local response
  response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=password&username=${AUTH_USERNAME}&password=${AUTH_PASSWORD}" \
    "${AUTH_ENDPOINT}")
  
  local http_code
  http_code=$(echo "$response" | tail -n1)
  local body
  body=$(echo "$response" | sed '$d')
  
  if [[ ! "$http_code" =~ ^2[0-9]{2}$ ]]; then
    log "ERROR" "Не удалось получить токен. HTTP $http_code"
    log "ERROR" "Ответ сервера: $body"
    exit 1
  fi
  
  if command -v python >/dev/null 2>&1; then
    AUTH_TOKEN=$(echo "$body" | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
  elif command -v jq >/dev/null 2>&1; then
    AUTH_TOKEN=$(echo "$body" | jq -r '.access_token')
  else
    log "ERROR" "Нужен python3 или jq для парсинга JSON"
    exit 1
  fi
  
  if [ -z "$AUTH_TOKEN" ]; then
    log "ERROR" "Токен пустой"
    exit 1
  fi
  
  log "INFO" "Токен получен (длина: ${#AUTH_TOKEN} символов)"
}

download_file() {
  local url=$1
  local output_file=$2
  local attempt=1
  
  while [ $attempt -le $MAX_RETRIES ]; do
    log "INFO" "Скачивание (попытка $attempt/$MAX_RETRIES): $url"

    if curl -sL -o "$output_file" "$url" \
      --fail \
      --connect-timeout 10 \
      --max-time 30 \
      --retry 0 \
      --show-error 2>>"$LOG_FILE"; then
      
      if [ -s "$output_file" ]; then
        log "INFO" "Файл скачан успешно"
        return 0
      else
        log "WARN" "Файл пустой. Повтор..."
        rm -f "$output_file"
      fi
    else
      local exit_code=$?
      log "WARN" "Ошибка скачивания (код: $exit_code). Повтор через $RETRY_DELAY сек..."
      rm -f "$output_file"
    fi
    
    sleep $RETRY_DELAY
    attempt=$((attempt + 1))
  done
  
  log "ERROR" "Не удалось скачать файл после $MAX_RETRIES попыток"
  return 1
}

upload_file() {
  local file_path=$1
  local file_name
  file_name=$(basename "$file_path")
  
  local http_code
  http_code=$(curl -s -o /tmp/upload_response.txt -w "%{http_code}" \
    -X POST \
    -H "Authorization: Bearer ${AUTH_TOKEN}" \
    -F "file=@${file_path};type=application/pdf" \
    "${UPLOAD_ENDPOINT}")
  
  if [[ "$http_code" =~ ^2[0-9]{2}$ ]]; then
    log "INFO" "Загружено: $file_name (HTTP $http_code)"
    return 0
  else
    log "ERROR" "Ошибка загрузки $file_name (HTTP $http_code)"
    if [ -f /tmp/upload_response.txt ]; then
      log "ERROR" "   Ответ: $(cat /tmp/upload_response.txt)"
    fi
    return 1
  fi
}

command -v curl >/dev/null 2>&1 || { log "ERROR" "curl не найден. Установите curl."; exit 1; }
command -v python >/dev/null 2>&1 || command -v jq >/dev/null 2>&1 || { 
  log "ERROR" "Нужен python3 или jq для парсинга JSON ответа авторизации"; exit 1 
}

wait_for_api

get_auth_token

mkdir -p "$TEST_DIR"
log "INFO" "Директория для кэша: $TEST_DIR"

success_count=0
error_count=0
total_files=${#PDF_URLS[@]}

log "INFO" "Начинаем обработку $total_files файлов..."

for i in "${!PDF_URLS[@]}"; do
  url="${PDF_URLS[$i]}"
  file_name="lecture_$((i + 1)).pdf"
  file_path="${TEST_DIR}/${file_name}"

  log "STEP" "----------------------------------------"
  log "STEP" "Файл $((i + 1))/$total_files"

  log "INFO" "Скачивание: $url"
  if ! download_file "$url" "$file_path"; then
    log "ERROR" "Не удалось скачать. Пропуск."
    error_count=$((error_count + 1))
    continue
  fi

  file_size=$(stat -f%z "$file_path" 2>/dev/null || stat -c%s "$file_path" 2>/dev/null)
  max_size=$((MAX_FILE_SIZE_MB * 1024 * 1024))
  if [ "$file_size" -gt "$max_size" ]; then
    log "WARN" "Файл слишком большой ($((file_size / 1024 / 1024)) МБ > $MAX_FILE_SIZE_MB МБ). Пропуск."
    error_count=$((error_count + 1))
    continue
  fi
  log "INFO" "Размер: $((file_size / 1024)) КБ"

  if upload_file "$file_path"; then
    success_count=$((success_count + 1))
  else
    error_count=$((error_count + 1))
  fi

  sleep 1
done

log "STEP" "Итоги инициализации:"
log "INFO" "Всего файлов:  $total_files"
log "INFO" "Успешно:       $success_count"
log "INFO" "Ошибок:        $error_count"

if [ $success_count -eq $total_files ]; then
  log "INFO" "Все файлы успешно загружены!"
  exit 0
elif [ $success_count -gt 0 ]; then
  log "WARN" "Загружена часть файлов. Подробности в $LOG_FILE"
  exit 0
else
  log "ERROR" "Не удалось загрузить ни один файл."
  exit 1
fi
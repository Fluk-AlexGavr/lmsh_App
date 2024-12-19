using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Networking;

namespace QRCodeApp
{
    public class TransactionManager : MonoBehaviour
    {
        public static TransactionManager Instance;
        [SerializeField] QRCodeManager qRCodeManager;

        public InputField scoreInputField;       // Поле ввода изменения счёта
        public Text transactionOutputText;       // Текст для вывода результата
        int userId;

        private const string backendUrl = "http://127.0.0.1:8000"; // URL бекенда

        void Awake()
        {
            if (Instance == null)
                Instance = this;
            else
                Destroy(gameObject);
        }

        // Метод для отправки изменения счёта на сервер
        public void SubmitScoreChange()
        {
            userId = qRCodeManager.PlayerIdNow();
            if (string.IsNullOrEmpty(scoreInputField.text))
            {
                transactionOutputText.text = "Введите значение изменения счёта!";
                return;
            }

            if (!int.TryParse(scoreInputField.text, out int scoreChange))
            {
                transactionOutputText.text = "Ошибка: Введите целое число!";
                return;
            }

            StartCoroutine(SendScoreUpdate(userId, scoreChange));
        }

        private IEnumerator SendScoreUpdate(int userId, int scoreChange)
        {
            string url = $"{backendUrl}/update-score";

            // Создаём объект данных для отправки
            var transactionData = new TransactionRequest
            {
                user_id = userId,
                score_change = scoreChange
            };

            string jsonData = JsonUtility.ToJson(transactionData);
            Debug.Log($"Отправляем JSON: {jsonData}");

            using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
            {
                request.SetRequestHeader("Content-Type", "application/json");
                request.uploadHandler = new UploadHandlerRaw(System.Text.Encoding.UTF8.GetBytes(jsonData));
                request.downloadHandler = new DownloadHandlerBuffer();

                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    Debug.Log($"Ответ сервера: {request.downloadHandler.text}");
                    var response = JsonUtility.FromJson<ScoreResponse>(request.downloadHandler.text);
                    transactionOutputText.text = $"Баланс обновлён! Новый счёт: {response.new_score}";
                }
                else
                {
                    Debug.LogError($"Ошибка сервера: {request.error}");
                    Debug.LogError($"Тело ответа: {request.downloadHandler.text}");
                    transactionOutputText.text = $"Ошибка: {request.error}";
                }
            }
        }
    }

    // Классы данных для сериализации JSON
    [System.Serializable]
    public class TransactionRequest
    {
        public int user_id;
        public int score_change;
    }

    [System.Serializable]
    public class ScoreResponse
    {
        public string message;
        public int new_score;
    }
}

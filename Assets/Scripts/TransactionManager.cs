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

        public InputField scoreInputField;       // ���� ����� ��������� �����
        public Text transactionOutputText;       // ����� ��� ������ ����������
        int userId;

        private const string backendUrl = "http://127.0.0.1:8000"; // URL �������

        void Awake()
        {
            if (Instance == null)
                Instance = this;
            else
                Destroy(gameObject);
        }

        // ����� ��� �������� ��������� ����� �� ������
        public void SubmitScoreChange()
        {
            userId = qRCodeManager.PlayerIdNow();
            if (string.IsNullOrEmpty(scoreInputField.text))
            {
                transactionOutputText.text = "������� �������� ��������� �����!";
                return;
            }

            if (!int.TryParse(scoreInputField.text, out int scoreChange))
            {
                transactionOutputText.text = "������: ������� ����� �����!";
                return;
            }

            StartCoroutine(SendScoreUpdate(userId, scoreChange));
        }

        private IEnumerator SendScoreUpdate(int userId, int scoreChange)
        {
            string url = $"{backendUrl}/update-score";

            // ������ ������ ������ ��� ��������
            var transactionData = new TransactionRequest
            {
                user_id = userId,
                score_change = scoreChange
            };

            string jsonData = JsonUtility.ToJson(transactionData);
            Debug.Log($"���������� JSON: {jsonData}");

            using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
            {
                request.SetRequestHeader("Content-Type", "application/json");
                request.uploadHandler = new UploadHandlerRaw(System.Text.Encoding.UTF8.GetBytes(jsonData));
                request.downloadHandler = new DownloadHandlerBuffer();

                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    Debug.Log($"����� �������: {request.downloadHandler.text}");
                    var response = JsonUtility.FromJson<ScoreResponse>(request.downloadHandler.text);
                    transactionOutputText.text = $"������ �������! ����� ����: {response.new_score}";
                }
                else
                {
                    Debug.LogError($"������ �������: {request.error}");
                    Debug.LogError($"���� ������: {request.downloadHandler.text}");
                    transactionOutputText.text = $"������: {request.error}";
                }
            }
        }
    }

    // ������ ������ ��� ������������ JSON
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

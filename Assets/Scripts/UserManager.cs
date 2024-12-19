using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Networking;

namespace QRCodeApp
{
    public class UserManager : MonoBehaviour
    {
        public static UserManager Instance;
        public Text userInfoText;
        public Transform userListContainer;
        public GameObject userListItemPrefab;

        private const string backendUrl = "http://127.0.0.1:8000";

        void Awake()
        {
            if (Instance == null)
            {
                Instance = this;
            }
            else
            {
                Destroy(gameObject);
            }
        }

        public void FetchUserData(string userId)
        {
            StartCoroutine(GetUserData(userId));
        }

        private IEnumerator GetUserData(string userId)
        {
            string url = $"{backendUrl}/user/{userId}";
            using (UnityWebRequest request = UnityWebRequest.Get(url))
            {
                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    User user = JsonUtility.FromJson<User>(request.downloadHandler.text);
                    userInfoText.text = $"Игрок называет себя: {user.full_name},\nКоличество очков игрока: {user.balance}";
                }
                else
                {
                    userInfoText.text = $"Error fetching user: {request.error}";
                }
            }
        }

        public void FetchAllUsers()
        {
            StartCoroutine(GetAllUsers());
        }

        private IEnumerator GetAllUsers()
        {
            string url = $"{backendUrl}/users";
            using (UnityWebRequest request = UnityWebRequest.Get(url))
            {
                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    List<User> users = JsonUtility.FromJson<UserList>(request.downloadHandler.text).users;
                    UpdateUserList(users);
                }
                else
                {
                    userInfoText.text = $"Error fetching users: {request.error}";
                }
            }
        }

        private void UpdateUserList(List<User> users)
        {
            foreach (Transform child in userListContainer)
            {
                Destroy(child.gameObject);
            }

            foreach (var user in users)
            {
                GameObject listItem = Instantiate(userListItemPrefab, userListContainer);
                listItem.GetComponentInChildren<Text>().text = $"{user.full_name} - {user.balance}";
            }
        }
    }
}

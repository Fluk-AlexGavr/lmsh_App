using System;
using System.Collections.Generic;

namespace QRCodeApp
{
    [System.Serializable]
    public class QRCodeData
    {
        public string id;
        public string full_name;
    }

    [System.Serializable]
    public class User
    {
        public string id;
        public string full_name;
        public int balance;
    }

    [System.Serializable]
    public class TransactionData
    {
        public string userId;
        public int amount;
    }

    [System.Serializable]
    public class UserList
    {
        public List<User> users;
    }
}

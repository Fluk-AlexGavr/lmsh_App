using System;
using Unity.VisualScripting;
using UnityEngine;
using UnityEngine.UI;
using ZXing;

namespace QRCodeApp
{
    public class QRCodeManager : MonoBehaviour
    {
        public RawImage cameraView;
        public Text qrOutputText;
        private int playerId;

        private WebCamTexture webcamTexture;

        void Start()
        {
            InitializeCamera();
        }

        void Update()
        {
            ScanQRCode();
        }

        private void InitializeCamera()
        {
            webcamTexture = new WebCamTexture();
            cameraView.texture = webcamTexture;
            webcamTexture.Play();
        }

        private void ScanQRCode()
        {
            if (webcamTexture.isPlaying)
            {
                try
                {
                    IBarcodeReader barcodeReader = new BarcodeReader();
                    var result = barcodeReader.Decode(webcamTexture.GetPixels32(), webcamTexture.width, webcamTexture.height);

                    if (result != null)
                    {
                        qrOutputText.text = $"В QR коде зашифровано: {result.Text}";
                        //webcamTexture.Stop();

                        QRCodeData qrData = JsonUtility.FromJson<QRCodeData>(result.Text);
                        UserManager.Instance.FetchUserData(qrData.id);
                        playerId =  Convert.ToInt32(qrData.id);
                    }
                }
                catch (System.Exception ex)
                {
                    Debug.LogWarning($"QR Code scanning failed: {ex.Message}");
                }
            }
        }

        public int PlayerIdNow()
        {
            return playerId;
        }
    }
}

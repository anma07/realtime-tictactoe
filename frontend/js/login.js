let stream;
const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const startBtn = document.getElementById("startBtn");
const captureBtn = document.getElementById("captureBtn");
const statusText = document.getElementById("status");

// STEP 1: Start camera
startBtn.onclick = async () => {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;

        await video.play(); 

        statusText.innerText = "Camera started";
    } catch (err) {
        statusText.innerText = "Camera access denied";
        console.error("Camera error:", err);
    }
};

// STEP 2: Capture image and send to backend
captureBtn.onclick = async () => {

    if (!video.videoWidth) { 
        statusText.innerText = "Camera not ready yet";
        return;
    }

    // Draw frame on canvas
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);

    // Convert to base64 (compressed)
    const imageData = canvas.toDataURL("image/jpeg", 0.8).split(",")[1];

    statusText.innerText = "Sending to server...";

    try {
        const response = await fetch("http://<YOUR_IP>:8000/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                image_data: imageData
            })
        });

        const data = await response.json();
        console.log("Response:", data);

        if (data.status === "success") {
            statusText.innerText = "Login successful!";
            localStorage.setItem("uid", data.uid);
            
            // Stop camera before redirect
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
            
            // FIXED: Redirect to lobby with uid in URL
            setTimeout(() => {
                window.location.href = `lobby.html?uid=${data.uid}`;
            }, 500);
        } else {
            statusText.innerText = `Login failed: ${data.reason || 'Unknown error'}`;
        }

    } catch (err) {
        statusText.innerText = "Server error";
        console.error(err);
    }
};
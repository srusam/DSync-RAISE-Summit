let recordedBlob;
let mediaRecorder;
let mediaChunks = [];

const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const saveBtn = document.getElementById("saveBtn");
const player = document.getElementById("preview");
const placeholder = document.getElementById("preview-placeholder");

const isVideo = window.location.search.includes("type=video");

function showPreview() {
    player.style.display = "block";
    if (placeholder) placeholder.style.display = "none";
}

startBtn.onclick = async () => {

    const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: isVideo
    });

    // Live preview for video
    if (isVideo) {
        player.srcObject = stream;
        showPreview();
        player.muted = true;
        player.play();
    }

    mediaRecorder = new MediaRecorder(stream);

    mediaChunks = [];

    mediaRecorder.ondataavailable = (event) => {
        mediaChunks.push(event.data);
    };

    mediaRecorder.onstop = () => {

        recordedBlob = new Blob(mediaChunks, {
            type: isVideo ? "video/webm" : "audio/webm"
        });

        // Stop live preview
        if (isVideo) {
            player.srcObject = null;
        }

        // Show recorded preview
        player.srcObject = null;
        player.src = URL.createObjectURL(recordedBlob);
        showPreview();

        saveBtn.style.display = "inline-block";

        // Stop webcam/mic
        stream.getTracks().forEach(track => track.stop());
    };

    mediaRecorder.start();

    startBtn.disabled = true;
    stopBtn.disabled = false;
};

stopBtn.onclick = () => {

    mediaRecorder.stop();

    startBtn.disabled = false;
    stopBtn.disabled = true;
};

saveBtn.onclick = async () => {

    saveBtn.disabled = true;
    saveBtn.innerText = "Saving...";

    const formData = new FormData();

    formData.append(
        "media",
        recordedBlob,
        "recording.webm"
    );

    const response = await fetch(window.location.href, {
        method: "POST",
        body: formData
    });

    if (response.ok) {
        window.location.href = response.url;
    } else {
        saveBtn.disabled = false;
        saveBtn.innerText = "💾 Save Recording";
        alert("Failed to save recording.");
    }
};
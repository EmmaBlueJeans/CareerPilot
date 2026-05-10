(function () {
    const form = document.getElementById('screen-form');
    const fileInput = document.getElementById('resume');
    const uploadLabel = document.getElementById('upload-label');
    const submitBtn = document.getElementById('submit-btn');
    const dropZone = document.querySelector('.upload');

    if (!form) return;

    fileInput.addEventListener('change', () => {
        if (fileInput.files && fileInput.files[0]) {
            uploadLabel.textContent = fileInput.files[0].name;
        }
    });

    ['dragenter', 'dragover'].forEach(evt => {
        dropZone.addEventListener(evt, e => {
            e.preventDefault(); e.stopPropagation();
            dropZone.classList.add('dragover');
        });
    });
    ['dragleave', 'drop'].forEach(evt => {
        dropZone.addEventListener(evt, e => {
            e.preventDefault(); e.stopPropagation();
            dropZone.classList.remove('dragover');
        });
    });
    dropZone.addEventListener('drop', e => {
        const dt = e.dataTransfer;
        if (dt && dt.files && dt.files[0]) {
            fileInput.files = dt.files;
            uploadLabel.textContent = dt.files[0].name;
        }
    });

    form.addEventListener('submit', () => {
        submitBtn.disabled = true;
        submitBtn.querySelector('.btn-label').textContent = 'Analyzing…';
        submitBtn.querySelector('.btn-spinner').hidden = false;
    });
})();

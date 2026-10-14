/* ========================================================
   GRWM — GET READY WITH ME
   Shared Frontend JavaScript (static/js/file.js)
   ======================================================== */

// Universal Toast Function
function showToast(message, type = 'normal') {
    let toast = document.getElementById('toast');
    let toastMessage = document.getElementById('toastMessage');

    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        toast.className = 'toast';
        toastMessage = document.createElement('span');
        toastMessage.id = 'toastMessage';
        toast.appendChild(toastMessage);
        document.body.appendChild(toast);
    }

    toast.className = 'toast show';
    if (type === 'error') {
        toast.classList.add('toast-error');
    } else if (type === 'success') {
        toast.classList.add('toast-success');
    }

    toastMessage.textContent = message;

    clearTimeout(window.toastTimer);
    window.toastTimer = setTimeout(() => {
        toast.classList.remove('show');
    }, 3500);
}

// Password Visibility Toggle
function setupPasswordToggle(inputId, buttonId) {
    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId);

    if (!input || !button) return;

    button.addEventListener('click', (e) => {
        e.preventDefault();
        if (input.type === 'password') {
            input.type = 'text';
            button.textContent = '🙈';
        } else {
            input.type = 'password';
            button.textContent = '👁️';
        }
    });
}

// Email Validation Helper
function validEmail(email) {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailPattern.test(email);
}

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    // Setup Password Toggles
    setupPasswordToggle('password', 'togglePassword');
    setupPasswordToggle('confirmPassword', 'toggleConfirmPassword');

    // Password Strength Meter
    const regPassword = document.getElementById('password');
    const strengthBar = document.getElementById('strengthBar');
    const strengthText = document.getElementById('strengthText');

    if (regPassword && strengthBar && strengthText) {
        regPassword.addEventListener('input', () => {
            const val = regPassword.value;
            let score = 0;
            if (val.length >= 6) score++;
            if (val.length >= 10) score++;
            if (/[A-Z]/.test(val)) score++;
            if (/[0-9]/.test(val)) score++;
            if (/[^A-Za-z0-9]/.test(val)) score++;

            strengthBar.style.width = (score * 20) + '%';
            if (score <= 1) {
                strengthBar.style.backgroundColor = '#ef4444';
                strengthText.textContent = 'Weak password';
            } else if (score === 2) {
                strengthBar.style.backgroundColor = '#f59e0b';
                strengthText.textContent = 'Fair password';
            } else if (score === 3) {
                strengthBar.style.backgroundColor = '#8b5cf6';
                strengthText.textContent = 'Good password';
            } else {
                strengthBar.style.backgroundColor = '#10b981';
                strengthText.textContent = 'Strong password ✨';
            }
        });
    }

    // Login Form Client-Side Validation (Preserves toast alerts and allows Flask submit)
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function (event) {
            const email = document.getElementById('email')?.value.trim();
            const password = document.getElementById('password')?.value;

            if (!email) {
                event.preventDefault();
                showToast('Please enter your email.', 'error');
                document.getElementById('email')?.focus();
                return;
            }

            if (!validEmail(email)) {
                event.preventDefault();
                showToast('Please enter a valid email address.', 'error');
                document.getElementById('email')?.focus();
                return;
            }

            if (!password) {
                event.preventDefault();
                showToast('Please enter your password.', 'error');
                document.getElementById('password')?.focus();
                return;
            }

            if (password.length < 6) {
                event.preventDefault();
                showToast('Password must contain at least 6 characters.', 'error');
                document.getElementById('password')?.focus();
                return;
            }
            // Valid inputs: allow natural submission to Flask POST /login
        });
    }

    // Register Form Client-Side Validation (Preserves toast alerts and allows Flask submit)
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function (event) {
            const name = document.getElementById('name')?.value.trim();
            const email = document.getElementById('email')?.value.trim();
            const password = document.getElementById('password')?.value;
            const confirmPassword = document.getElementById('confirmPassword')?.value || document.getElementById('confirm_password')?.value;
            const terms = document.getElementById('terms')?.checked;

            if (!name) {
                event.preventDefault();
                showToast('Please enter your name.', 'error');
                document.getElementById('name')?.focus();
                return;
            }

            if (!email || !validEmail(email)) {
                event.preventDefault();
                showToast('Please enter a valid email.', 'error');
                document.getElementById('email')?.focus();
                return;
            }

            if (!password || password.length < 6) {
                event.preventDefault();
                showToast('Password must contain at least 6 characters.', 'error');
                document.getElementById('password')?.focus();
                return;
            }

            if (password !== confirmPassword) {
                event.preventDefault();
                showToast('Passwords do not match.', 'error');
                document.getElementById('confirmPassword')?.focus();
                return;
            }

            if (!terms) {
                event.preventDefault();
                showToast('Please accept the Terms & Conditions.', 'error');
                document.getElementById('terms')?.focus();
                return;
            }
            // Valid inputs: allow natural submission to Flask POST /signup
        });
    }

    // Wardrobe Photo Preview
    const itemPhoto = document.getElementById('itemPhoto');
    const photoPreview = document.getElementById('photoPreview');
    if (itemPhoto && photoPreview) {
        itemPhoto.addEventListener('change', function () {
            const file = this.files[0];
            if (!file) {
                photoPreview.innerHTML = '<span>📸 Select a photo of your clothing</span>';
                return;
            }
            if (!file.type.startsWith('image/')) {
                showToast('Please select a valid image file (PNG, JPG, WebP).', 'error');
                this.value = '';
                return;
            }
            if (file.size > 5 * 1024 * 1024) {
                showToast('Image size exceeds 5MB limit.', 'error');
                this.value = '';
                return;
            }
            const reader = new FileReader();
            reader.onload = (e) => {
                photoPreview.innerHTML = `<img src="${e.target.result}" alt="Clothing Preview">`;
            };
            reader.readAsDataURL(file);
        });
    }

    // Edit Item Modal Photo Preview
    const editItemPhoto = document.getElementById('editItemPhoto');
    const editPhotoPreview = document.getElementById('editPhotoPreview');
    if (editItemPhoto && editPhotoPreview) {
        editItemPhoto.addEventListener('change', function () {
            const file = this.files[0];
            if (file) {
                if (!file.type.startsWith('image/')) {
                    showToast('Please select a valid image file.', 'error');
                    this.value = '';
                    return;
                }
                const reader = new FileReader();
                reader.onload = (e) => {
                    editPhotoPreview.innerHTML = `<img src="${e.target.result}" alt="New Preview">`;
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Profile Photo Live Preview
    const photoInput = document.getElementById('photoInput');
    const profilePhoto = document.getElementById('profilePhoto');
    if (photoInput && profilePhoto) {
        photoInput.addEventListener('change', function () {
            const file = this.files[0];
            if (!file) return;
            if (!file.type.startsWith('image/')) {
                showToast('Please upload an image file.', 'error');
                this.value = '';
                return;
            }
            if (file.size > 5 * 1024 * 1024) {
                showToast('Profile image must be less than 5MB.', 'error');
                this.value = '';
                return;
            }
            const reader = new FileReader();
            reader.onload = (e) => {
                profilePhoto.src = e.target.result;
            };
            reader.readAsDataURL(file);

            // Automatically submit profile photo form if present
            const photoForm = document.getElementById('profilePhotoForm');
            if (photoForm) {
                showToast('Uploading profile photo...', 'normal');
                photoForm.submit();
            }
        });
    }

    // Wardrobe Search and Filter
    const searchInput = document.getElementById('wardrobeSearch');
    const categoryFilter = document.getElementById('wardrobeCategoryFilter');
    const styleFilter = document.getElementById('wardrobeStyleFilter');
    const wardrobeGrid = document.getElementById('wardrobeGrid');

    function filterWardrobe() {
        if (!wardrobeGrid) return;
        const query = (searchInput ? searchInput.value : '').toLowerCase().trim();
        const selectedCat = (categoryFilter ? categoryFilter.value : '').toLowerCase();
        const selectedStyle = (styleFilter ? styleFilter.value : '').toLowerCase();

        const items = wardrobeGrid.querySelectorAll('.wardrobe-item');
        let visibleCount = 0;

        items.forEach((item) => {
            const name = (item.dataset.name || '').toLowerCase();
            const cat = (item.dataset.category || '').toLowerCase();
            const style = (item.dataset.style || '').toLowerCase();

            const matchesSearch = !query || name.includes(query) || cat.includes(query) || style.includes(query);
            const matchesCat = !selectedCat || cat === selectedCat;
            const matchesStyle = !selectedStyle || style === selectedStyle;

            if (matchesSearch && matchesCat && matchesStyle) {
                item.style.display = 'flex';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });

        const emptyMessage = document.getElementById('noFilterResults');
        if (emptyMessage) {
            emptyMessage.style.display = (visibleCount === 0 && items.length > 0) ? 'block' : 'none';
        }
    }

    if (searchInput) searchInput.addEventListener('input', filterWardrobe);
    if (categoryFilter) categoryFilter.addEventListener('change', filterWardrobe);
    if (styleFilter) styleFilter.addEventListener('change', filterWardrobe);

    // Style Me / Recommendation URL query prefill
    const params = new URLSearchParams(window.location.search);
    const occasionParam = params.get('occasion');
    if (occasionParam) {
        const matchingRadio = document.querySelector(`input[name="occasion"][value="${occasionParam}"]`);
        if (matchingRadio) matchingRadio.checked = true;
    }

    // ── Virtual Try-On Interactive Flow (IDM-VTON) ──────────────────────
    const tryOnBtn = document.getElementById('generateLookBtn');
    const consentCheckbox = document.getElementById('tryOnConsent');
    const tryOnResultArea = document.getElementById('tryOnResult');
    const sourceWardrobeRadio = document.getElementById('sourceWardrobe');
    const sourceUploadRadio = document.getElementById('sourceUpload');
    const wardrobeSelectContainer = document.getElementById('wardrobeSelectContainer');
    const clothingUploadContainer = document.getElementById('clothingUploadContainer');
    const tryOnPersonFileInput = document.getElementById('tryOnPersonFile');
    const tryOnPersonPreview = document.getElementById('tryOnPersonPreview');
    const tryOnPersonPreviewImg = document.getElementById('tryOnPersonPreviewImg');
    const tryOnGarmentFileInput = document.getElementById('tryOnGarmentFile');
    const tryOnGarmentPreview = document.getElementById('tryOnGarmentPreview');
    const tryOnGarmentPreviewImg = document.getElementById('tryOnGarmentPreviewImg');
    const tryOnCategorySelect = document.getElementById('tryOnCategorySelect');
    const tryOnGarmentDesc = document.getElementById('tryOnGarmentDesc');

    // Toggle between Wardrobe selection and direct clothing upload
    if (sourceWardrobeRadio && sourceUploadRadio) {
        sourceWardrobeRadio.addEventListener('change', () => {
            if (sourceWardrobeRadio.checked) {
                if (wardrobeSelectContainer) wardrobeSelectContainer.style.display = 'block';
                if (clothingUploadContainer) clothingUploadContainer.style.display = 'none';
            }
        });
        sourceUploadRadio.addEventListener('change', () => {
            if (sourceUploadRadio.checked) {
                if (wardrobeSelectContainer) wardrobeSelectContainer.style.display = 'none';
                if (clothingUploadContainer) clothingUploadContainer.style.display = 'block';
            }
        });
    }

    // Live preview for session person photo upload
    if (tryOnPersonFileInput && tryOnPersonPreview && tryOnPersonPreviewImg) {
        tryOnPersonFileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    tryOnPersonPreviewImg.src = e.target.result;
                    tryOnPersonPreview.style.display = 'flex';
                };
                reader.readAsDataURL(file);
            } else {
                tryOnPersonPreview.style.display = 'none';
            }
        });
    }

    // Live preview for session clothing photo upload
    if (tryOnGarmentFileInput && tryOnGarmentPreview && tryOnGarmentPreviewImg) {
        tryOnGarmentFileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    tryOnGarmentPreviewImg.src = e.target.result;
                    tryOnGarmentPreview.style.display = 'flex';
                };
                reader.readAsDataURL(file);
            } else {
                tryOnGarmentPreview.style.display = 'none';
            }
        });
    }

    if (tryOnBtn) {
        tryOnBtn.addEventListener('click', async () => {
            if (consentCheckbox && !consentCheckbox.checked) {
                showToast('Please check the consent box to process your photo for try-on.', 'error');
                consentCheckbox.focus();
                return;
            }

            const isUploadSource = sourceUploadRadio && sourceUploadRadio.checked;
            if (isUploadSource) {
                if (!tryOnGarmentFileInput || !tryOnGarmentFileInput.files || tryOnGarmentFileInput.files.length === 0) {
                    showToast('Please select a clothing image to upload.', 'error');
                    tryOnGarmentFileInput?.focus();
                    return;
                }
            }

            const formData = new FormData();
            formData.append('consent_given', 'true');

            // Attach personal photo if a custom one is selected for this session
            if (tryOnPersonFileInput && tryOnPersonFileInput.files && tryOnPersonFileInput.files.length > 0) {
                formData.append('person_image', tryOnPersonFileInput.files[0]);
            }

            if (isUploadSource) {
                formData.append('garment_image', tryOnGarmentFileInput.files[0]);
                formData.append('category', tryOnCategorySelect?.value || 'Tops');
                formData.append('garment_description', (tryOnGarmentDesc?.value || '').trim() || 'Custom Garment');
            } else {
                const outfitId = document.getElementById('tryOnOutfitSelect')?.value || 'current';
                formData.append('outfit_id', outfitId);
            }

            tryOnBtn.disabled = true;
            tryOnBtn.innerHTML = '⏳ Generating with IDM-VTON...';

            if (tryOnResultArea) {
                tryOnResultArea.style.display = 'block';
                tryOnResultArea.innerHTML = `
                    <div style="background:#f5f3ff; border-radius:18px; padding:30px; text-align:center; margin-top:20px; border:1px solid #ddd6fe;">
                        <div style="font-size:36px; margin-bottom:12px;">🪡</div>
                        <p style="font-weight:600; color:#4c1d95; font-size:16px;">IDM-VTON is generating your virtual try-on...</p>
                        <p style="font-size:13px; color:var(--muted); max-width:480px; margin:8px auto 0;">
                            Improving Diffusion Models (IDM-VTON) is processing your photo and garment. This typically takes 30–60 seconds on the ZeroGPU pipeline.
                        </p>
                    </div>`;
            }

            try {
                const response = await fetch('/api/virtual-tryon', {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: formData
                });

                const rawText = await response.text();
                let data;
                try {
                    data = JSON.parse(rawText);
                } catch (_) {
                    const statusMsg = `Server returned HTTP ${response.status}. ${response.status === 302 || (response.status === 200 && rawText.includes('<html')) ? 'Your session may have expired. Please refresh and log in again.' : rawText.slice(0, 200)}`;
                    showToast(statusMsg, 'error');
                    if (tryOnResultArea) {
                        tryOnResultArea.style.display = 'block';
                        tryOnResultArea.innerHTML = `
                            <div style="background:#fff1f2; border:1px solid #fecdd3; border-radius:14px; padding:18px; margin-top:16px; text-align:left;">
                                <strong style="color:#be123c;">⚠️ Server Error</strong>
                                <p style="color:#9f1239; font-size:13px; margin-top:8px;">${statusMsg}</p>
                            </div>`;
                    }
                    return;
                }

                if (response.status === 401) {
                    const loginMsg = data.error || 'Session expired. Please log in again.';
                    showToast(loginMsg, 'error');
                    if (tryOnResultArea) {
                        tryOnResultArea.style.display = 'block';
                        tryOnResultArea.innerHTML = `
                            <div style="background:#fff1f2; border:1px solid #fecdd3; border-radius:14px; padding:18px; margin-top:16px; text-align:left;">
                                <strong style="color:#be123c;">🔐 Session Expired</strong>
                                <p style="color:#9f1239; font-size:13px; margin-top:8px;">${loginMsg}</p>
                                <a href="/login" style="display:inline-block; margin-top:10px; color:#7c3aed; font-weight:600; font-size:13px;">→ Go to Login</a>
                            </div>`;
                    }
                    return;
                }

                if (data.success && data.generated_image) {
                    showToast(data.message || 'Virtual Try-On complete! ✨', 'success');
                    if (tryOnResultArea) {
                        tryOnResultArea.style.display = 'block';
                        tryOnResultArea.innerHTML = `
                            <div style="background:white; border-radius:18px; padding:24px; border:1px solid var(--border); margin-top:20px; box-shadow:var(--shadow-soft); text-align:center;">
                                <span class="tryon-status-badge">✦ IDM-VTON Virtual Try-On</span>
                                <h4 style="font-family:'Playfair Display',serif; font-size:22px; margin:8px 0; color:var(--purple);">✨ Your Virtual Try-On</h4>
                                <p style="color:var(--muted); font-size:13px; margin-bottom:16px;">
                                    Wearing: <strong>${data.clothing_item || 'Selected Item'}</strong> ${data.category ? `(${data.category})` : ''}
                                </p>
                                <div style="max-width:380px; margin:0 auto; border-radius:16px; overflow:hidden; box-shadow:0 8px 30px rgba(139,92,246,0.18); border:1px solid var(--border);">
                                    <img src="${data.generated_image}" alt="Virtual Try-On Result"
                                         style="width:100%; display:block; object-fit:cover;"
                                         onerror="this.parentElement.innerHTML='<p style=\\'color:#be123c;padding:20px\\'>Image failed to load. Please try again.</p>'">
                                </div>
                                <div style="margin-top:16px; display:flex; justify-content:center; gap:12px; flex-wrap:wrap;">
                                    <a href="${data.generated_image}" download="grwm_idm_vton_result.png" class="primary-btn" style="text-decoration:none; padding:10px 22px; font-size:13px; display:inline-flex; align-items:center; gap:6px;">
                                        ⬇️ Download Result
                                    </a>
                                </div>
                                <p style="font-size:11px; color:var(--muted); margin-top:14px;">
                                    Authentic virtual try-on synthesized with IDM-VTON diffusion model
                                </p>
                            </div>`;
                    }
                } else {
                    const errMsg = data.error || 'Virtual try-on generation failed.';
                    showToast(errMsg, 'error');
                    if (tryOnResultArea) {
                        tryOnResultArea.style.display = 'block';
                        tryOnResultArea.innerHTML = `
                            <div style="background:#fff1f2; border:1px solid #fecdd3; border-radius:14px; padding:18px; margin-top:16px; text-align:left;">
                                <strong style="color:#be123c;">⚠️ Try-On Failed</strong>
                                <p style="color:#9f1239; font-size:13px; margin-top:8px;">${errMsg}</p>
                            </div>`;
                    }
                }
            } catch (err) {
                const netErr = `Connection failed: ${err.message || err}. Make sure Flask is running on http://127.0.0.1:5000`;
                showToast(netErr, 'error');
                if (tryOnResultArea) {
                    tryOnResultArea.style.display = 'block';
                    tryOnResultArea.innerHTML = `
                        <div style="background:#fff1f2; border:1px solid #fecdd3; border-radius:14px; padding:18px; margin-top:16px;">
                            <strong style="color:#be123c;">⚠️ Connection Failed</strong>
                            <p style="color:#9f1239; font-size:13px; margin-top:8px;">${netErr}</p>
                        </div>`;
                }
            } finally {
                tryOnBtn.disabled = false;
                tryOnBtn.innerHTML = '✨ Generate My Look';
            }
        });
    }
});

// Edit Wardrobe Item Modal Controls
function openEditModal(item) {
    const modal = document.getElementById('editModal');
    if (!modal) return;

    document.getElementById('editItemId').value = item.id;
    document.getElementById('editItemName').value = item.name;
    document.getElementById('editItemCategory').value = item.category;
    document.getElementById('editItemColor').value = item.color;
    document.getElementById('editItemStyle').value = item.style;
    document.getElementById('editItemDescription').value = item.description || '';

    const preview = document.getElementById('editPhotoPreview');
    if (preview) {
        if (item.image_path) {
            preview.innerHTML = `<img src="${item.image_path}" alt="${item.name}">`;
        } else {
            preview.innerHTML = '<span>No current image. Choose a file below to set one.</span>';
        }
    }

    const editForm = document.getElementById('editWardrobeForm');
    if (editForm) {
        editForm.action = `/wardrobe/${item.id}/edit`;
    }

    modal.classList.add('show');
}

function closeEditModal() {
    const modal = document.getElementById('editModal');
    if (modal) modal.classList.remove('show');
}

// Confirmation before deleting an item
function confirmDelete(itemName) {
    return confirm(`Are you sure you want to remove "${itemName}" from your wardrobe?`);
}

// Save outfit to favorites from result page
async function saveToFavorites(btn) {
    const recId = btn.dataset.recId;
    btn.disabled = true;
    btn.textContent = 'Saving...';

    try {
        const response = await fetch('/favorites/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ recommendation_id: recId })
        });
        const res = await response.json();
        if (res.success) {
            showToast('Saved to your favorites! 💖', 'success');
            btn.textContent = '💖 Saved to Favorites';
            btn.style.background = '#15803d';
        } else {
            showToast(res.error || 'Could not save to favorites.', 'error');
            btn.disabled = false;
            btn.textContent = '💖 Save to Favorites';
        }
    } catch (e) {
        showToast('Error saving favorite outfit.', 'error');
        btn.disabled = false;
        btn.textContent = '💖 Save to Favorites';
    }
}

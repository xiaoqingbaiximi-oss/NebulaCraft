/**
 * NebulaCraft 3D Preview Component
 * Uses Three.js CDN (unpkg, loaded on demand only)
 */
const TDViewer = {
    threeLoaded: false,
    loadingPromise: null,

    loadThree() {
        if (this.threeLoaded) return Promise.resolve(true);
        if (this.loadingPromise) return this.loadingPromise;
        this.loadingPromise = new Promise((resolve) => {
            if (window.THREE && window.THREE.GLTFLoader) {
                this.threeLoaded = true;
                resolve(true);
                return;
            }
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/three@0.157.0/build/three.min.js';
            script.onload = () => {
                const loaderScript = document.createElement('script');
                loaderScript.src = 'https://unpkg.com/three@0.157.0/examples/js/loaders/GLTFLoader.js';
                loaderScript.onload = () => { this.threeLoaded = true; resolve(true); };
                loaderScript.onerror = () => resolve(false);
                document.head.appendChild(loaderScript);
            };
            script.onerror = () => resolve(false);
            document.head.appendChild(script);
        });
        return this.loadingPromise;
    },

    async createPreview(glbBase64, container) {
        if (!container) return;
        const card = document.createElement('div');
        card.className = 'td-preview-card';
        card.style.cssText = 'width:300px;max-width:90vw;height:350px;border-radius:12px;background:var(--bg-secondary,#1e1e2e);border:1px solid var(--border-color,#333);overflow:hidden;margin:8px 0;position:relative;';
        const toolbar = document.createElement('div');
        toolbar.style.cssText = 'padding:8px 12px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--border-color,#333);';
        toolbar.innerHTML = '<span style="font-size:13px;font-weight:600;">🎮 3D Preview</span><button class="td-btn-download" style="background:var(--accent-color,#6c5ce7);color:white;border:none;padding:4px 12px;border-radius:6px;cursor:pointer;font-size:12px;">⬇ Download .glb</button>';
        const canvasContainer = document.createElement('div');
        canvasContainer.id = 'td-canvas-' + Date.now();
        canvasContainer.style.cssText = 'width:100%;height:calc(100% - 45px);';
        card.appendChild(toolbar);
        card.appendChild(canvasContainer);
        container.appendChild(card);
        toolbar.querySelector('.td-btn-download').onclick = () => { this.downloadModel(glbBase64); };
        const loaded = await this.loadThree();
        if (loaded) {
            this.renderModel(canvasContainer.id, glbBase64);
        } else {
            canvasContainer.innerHTML = '<div style="text-align:center;padding-top:50px;"><p>⚠️ 3D library failed to load</p><p style="font-size:12px;color:#888;">Network may be restricted</p><button onclick="TDViewer.downloadModel(\'' + glbBase64.substring(0, 50) + '...\')" style="margin-top:10px;background:var(--accent-color,#6c5ce7);color:white;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;">⬇ Download .glb file</button></div>';
            // Fix download button - store full base64
            const dlBtn = canvasContainer.querySelector('button');
            if (dlBtn) {
                dlBtn.onclick = () => { this.downloadModel(glbBase64); };
            }
        }
    },

    renderModel(containerId, glbBase64) {
        const container = document.getElementById(containerId);
        if (!container) return;
        const width = container.clientWidth;
        const height = container.clientHeight;
        const scene = new THREE.Scene();
        const isDark = document.body.classList.contains('dark-theme') || document.documentElement.getAttribute('data-theme') === 'dark';
        scene.background = new THREE.Color(isDark ? '#1e1e2e' : '#f0f0f0');
        const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
        camera.position.set(2, 1.5, 3);
        camera.lookAt(0, 0, 0);
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        container.appendChild(renderer.domElement);
        scene.add(new THREE.AmbientLight(0xffffff, 0.6));
        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight.position.set(5, 5, 5);
        scene.add(dirLight);
        const gridHelper = new THREE.GridHelper(2, 20, 0x888888, 0x444444);
        scene.add(gridHelper);
        const glbBinary = this._base64ToArrayBuffer(glbBase64);
        const loader = new THREE.GLTFLoader();
        loader.parse(glbBinary, '', (gltf) => {
            const model = gltf.scene;
            const box = new THREE.Box3().setFromObject(model);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            const maxDim = Math.max(size.x, size.y, size.z);
            const scale = maxDim > 0 ? 1.5 / maxDim : 1;
            model.scale.setScalar(scale);
            model.position.sub(center.multiplyScalar(scale));
            scene.add(model);
            const animate = () => {
                if (!container.isConnected) return;
                requestAnimationFrame(animate);
                model.rotation.y += 0.005;
                renderer.render(scene, camera);
            };
            animate();
        }, (error) => {
            console.error('3D model load failed:', error);
            container.innerHTML = '<p style="text-align:center;padding-top:40px;">⚠️ Model load failed</p>';
        });
    },

    downloadModel(glbBase64) {
        const binaryString = atob(glbBase64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) { bytes[i] = binaryString.charCodeAt(i); }
        const blob = new Blob([bytes], { type: 'model/gltf-binary' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'model.glb';
        link.click();
        URL.revokeObjectURL(link.href);
    },

    _base64ToArrayBuffer(base64) {
        const binaryString = atob(base64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) { bytes[i] = binaryString.charCodeAt(i); }
        return bytes.buffer;
    }
};

window.TDViewer = TDViewer;
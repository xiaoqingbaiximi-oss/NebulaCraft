"""
NebulaCraft 内置3D生成引擎（纯本地版）
无需网络下载，纯 numpy + Pillow + open3d
已适配项目结构：image_gen.py, data/output/ai_images/
"""
import os
import json
import base64
import logging
import numpy as np
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageFilter

logger = logging.getLogger(__name__)

MODEL_DIR = Path("data/models3d")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

_open3d = None

def _get_open3d():
    global _open3d
    if _open3d is None:
        import open3d as o3d
        _open3d = o3d
    return _open3d

def _estimate_depth_local(image: Image.Image) -> np.ndarray:
    """
    纯本地深度估计算法（不需要 MiDaS，不需要网络）
    基于：亮度 + 边缘检测 + 高斯模糊
    """
    gray = image.convert("L")
    img_array = np.array(gray, dtype=np.float32) / 255.0

    # 索贝尔边缘检测
    from scipy.ndimage import sobel
    edges_x = sobel(img_array, axis=0)
    edges_y = sobel(img_array, axis=1)
    edges = np.sqrt(edges_x**2 + edges_y**2)
    edges = np.clip(edges, 0, 1)

    # 深度：亮的地方近，边缘的地方远
    depth = img_array * 0.6 + (1 - edges) * 0.4
    depth = np.clip(depth, 0.05, 1.0)

    # 高斯模糊平滑
    from scipy.ndimage import gaussian_filter
    depth = gaussian_filter(depth, sigma=1.5)

    return depth.astype(np.float32)

def _depth_to_mesh(image: Image.Image, depth_map: np.ndarray, output_path: str):
    o3d = _get_open3d()
    img_array = np.array(image)
    if img_array.shape[-1] == 4:
        img_array = img_array[:, :, :3]

    depth_o3d = o3d.geometry.Image((depth_map * 1000).astype(np.uint16))
    color_o3d = o3d.geometry.Image(img_array.astype(np.uint8))

    rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
        color_o3d, depth_o3d,
        depth_scale=1000.0,
        depth_trunc=10.0,
        convert_rgb_to_intensity=False
    )

    h, w = depth_map.shape
    fx = fy = max(h, w)
    cx, cy = w / 2, h / 2
    intrinsic = o3d.camera.PinholeCameraIntrinsic(w, h, fx, fy, cx, cy)

    pcd = o3d.geometry.PointCloud.create_from_rgbd_image(rgbd, intrinsic)
    pcd.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.01, max_nn=30)
    )

    mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=8)

    vertices_to_remove = densities < np.quantile(densities, 0.1)
    mesh.remove_vertices_by_mask(vertices_to_remove)

    target_triangles = min(50000, len(mesh.triangles))
    if target_triangles > 0:
        mesh = mesh.simplify_quadric_decimation(target_triangles)

    o3d.io.write_triangle_mesh(output_path, mesh, write_ascii=False, compressed=True)
    logger.info(f"[3D] Mesh saved: {output_path}")

class TdEngine:
    @staticmethod
    def image_to_3d(image_input, task_id: str) -> dict:
        try:
            if isinstance(image_input, str):
                if image_input.startswith("data:") or len(image_input) > 500:
                    if "," in image_input:
                        image_input = image_input.split(",")[-1]
                    img_data = base64.b64decode(image_input)
                    image = Image.open(BytesIO(img_data)).convert("RGB")
                else:
                    image = Image.open(image_input).convert("RGB")
            elif isinstance(image_input, Image.Image):
                image = image_input.convert("RGB")
            else:
                return {"ok": False, "error": "Unsupported image input type"}

            max_size = 512
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
                image = image.resize(new_size, Image.LANCZOS)

            logger.info(f"[3D] Depth estimation ({image.size[0]}x{image.size[1]})")
            depth_map = _estimate_depth_local(image)

            logger.info("[3D] Mesh reconstruction...")
            output_dir = MODEL_DIR / task_id
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "model.glb"
            _depth_to_mesh(image, depth_map, str(output_path))

            with open(output_path, "rb") as f:
                glb_base64 = base64.b64encode(f.read()).decode("utf-8")

            logger.info(f"[3D] Success! task_id={task_id}")
            return {
                "ok": True,
                "model_base64": glb_base64,
                "format": "glb",
                "task_id": task_id,
                "download_url": f"/api/3d/download/{task_id}"
            }
        except ImportError as e:
            logger.error(f"Missing dependency: {e}")
            return {"ok": False, "error": f"Missing dependencies. Run: pip install open3d numpy scipy Pillow"}
        except Exception as e:
            logger.error(f"3D generation failed: {e}", exc_info=True)
            return {"ok": False, "error": f"Generation failed: {str(e)}"}

    @staticmethod
    def text_to_3d(prompt: str, task_id: str) -> dict:
        # 适配 image_gen.py
        from server.services.image_gen import image_gen

        logger.info(f"[3D] Text-to-3D: generating initial image -> {prompt}")
        img_result = image_gen.generate(prompt, style="realistic", width=512, height=512)

        if not img_result.get("ok"):
            return {"ok": False, "error": f"Initial image generation failed: {img_result.get('error', 'Unknown error')}"}

        url = img_result.get("url", "")
        if url:
            # 适配 data/output/ai_images/
            img_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data", url.lstrip("/").replace("/", os.sep)
            )
            if os.path.exists(img_path):
                return TdEngine.image_to_3d(img_path, task_id)

        logger.warning(f"[3D] Could not load generated image from disk. URL: {url}")
        return {"ok": False, "error": f"Image generated but could not be loaded from disk. URL: {url}"}

    @staticmethod
    def get_model_file(task_id: str) -> Path | None:
        output_dir = MODEL_DIR / task_id
        if not output_dir.exists():
            return None
        glb_files = list(output_dir.glob("*.glb"))
        return glb_files[0] if glb_files else None

td_engine = TdEngine()
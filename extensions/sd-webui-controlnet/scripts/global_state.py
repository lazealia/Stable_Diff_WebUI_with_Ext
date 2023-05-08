import os.path
import stat
import functools
from collections import OrderedDict

from modules import shared, scripts, sd_models
from modules.paths import models_path
from scripts.processor import *

CN_MODEL_EXTS = [".pt", ".pth", ".ckpt", ".safetensors"]
cn_models_dir = os.path.join(models_path, "ControlNet")
cn_models_dir_old = os.path.join(scripts.basedir(), "models")
cn_models = OrderedDict()      # "My_Lora(abcd1234)" -> C:/path/to/model.safetensors
cn_models_names = {}  # "my_lora" -> "My_Lora(abcd1234)"

cn_preprocessor_modules = {
    "none": lambda x, *args, **kwargs: (x, True),
    "canny": canny,
    "depth": midas,
    "depth_leres": functools.partial(leres, boost=False),
    "depth_leres++": functools.partial(leres, boost=True),
    "hed": hed,
    "hed_safe": hed_safe,
    "mediapipe_face": mediapipe_face,
    "mlsd": mlsd,
    "normal_map": midas_normal,
    "openpose": functools.partial(g_openpose_model.run_model, include_body=True, include_hand=False, include_face=False),
    "openpose_hand": functools.partial(g_openpose_model.run_model, include_body=True, include_hand=True, include_face=False),
    "openpose_face": functools.partial(g_openpose_model.run_model, include_body=True, include_hand=False, include_face=True),
    "openpose_faceonly": functools.partial(g_openpose_model.run_model, include_body=False, include_hand=False, include_face=True),
    "openpose_full": functools.partial(g_openpose_model.run_model, include_body=True, include_hand=True, include_face=True),
    "clip_vision": clip,
    "color": color,
    "pidinet": pidinet,
    "pidinet_safe": pidinet_safe,
    "pidinet_sketch": pidinet_ts,
    "pidinet_scribble": scribble_pidinet,
    # "scribble_thr": scribble_thr, # Removed by Lvmin to avoid confusing
    "scribble_xdog": scribble_xdog,
    "scribble_hed": scribble_hed,
    "segmentation": uniformer,
    # "binary": binary, # Removed by Lvmin to avoid confusing
    "threshold": threshold,
    "depth_zoe": zoe_depth,
    "normal_bae": normal_bae,
    "oneformer_coco": oneformer_coco,
    "oneformer_ade20k": oneformer_ade20k,
    "lineart": lineart,
    "lineart_coarse": lineart_coarse,
    "lineart_anime": lineart_anime,
    "lineart_standard": lineart_standard,
    "shuffle": shuffle,
    "tile_resample": tile_resample,
    "inpaint": inpaint,
    "invert": invert,
    "lineart_anime_denoise": lineart_anime_denoise
}

cn_preprocessor_unloadable = {
    "hed": unload_hed,
    "fake_scribble": unload_hed,
    "mlsd": unload_mlsd,
    "clip": unload_clip,
    "depth": unload_midas,
    "depth_leres": unload_leres,
    "normal_map": unload_midas,
    "pidinet": unload_pidinet,
    "openpose": g_openpose_model.unload,
    "openpose_hand": g_openpose_model.unload,
    "openpose_face": g_openpose_model.unload,
    "openpose_full": g_openpose_model.unload,
    "segmentation": unload_uniformer,
    "depth_zoe": unload_zoe_depth,
    "normal_bae": unload_normal_bae,
    "oneformer_coco": unload_oneformer_coco,
    "oneformer_ade20k": unload_oneformer_ade20k,
    "lineart": unload_lineart,
    "lineart_coarse": unload_lineart_coarse,
    "lineart_anime": unload_lineart_anime,
    "lineart_anime_denoise": unload_lineart_anime_denoise
}

preprocessor_aliases = {
    "invert": "invert (from white bg & black line)",
    "lineart_standard": "lineart_standard (from white bg & black line)",
    "lineart": "lineart_realistic",
    "color": "t2ia_color_grid",
    "clip_vision": "t2ia_style_clipvision",
    "pidinet_sketch": "t2ia_sketch_pidi",
    "depth": "depth_midas",
    "normal_map": "normal_midas",
    "hed": "softedge_hed",
    "hed_safe": "softedge_hedsafe",
    "pidinet": "softedge_pidinet",
    "pidinet_safe": "softedge_pidisafe",
    "segmentation": "seg_ufade20k",
    "oneformer_coco": "seg_ofcoco",
    "oneformer_ade20k": "seg_ofade20k",
    "pidinet_scribble": "scribble_pidinet",
    "inpaint": "inpaint_global_harmonious",
}

ui_preprocessor_keys = ['none', preprocessor_aliases['invert']]
ui_preprocessor_keys += sorted([preprocessor_aliases.get(k, k)
                                for k in cn_preprocessor_modules.keys()
                                if preprocessor_aliases.get(k, k) not in ui_preprocessor_keys])

reverse_preprocessor_aliases = {preprocessor_aliases[k]: k for k in preprocessor_aliases.keys()}


default_conf = os.path.join("models", "cldm_v15.yaml")
default_conf_adapter = os.path.join("models", "t2iadapter_sketch_sd14v1.yaml")
cn_detectedmap_dir = os.path.join("detected_maps")
default_detectedmap_dir = cn_detectedmap_dir
script_dir = scripts.basedir()

os.makedirs(cn_models_dir, exist_ok=True)
os.makedirs(cn_detectedmap_dir, exist_ok=True)


def traverse_all_files(curr_path, model_list):
    f_list = [(os.path.join(curr_path, entry.name), entry.stat())
              for entry in os.scandir(curr_path)]
    for f_info in f_list:
        fname, fstat = f_info
        if os.path.splitext(fname)[1] in CN_MODEL_EXTS:
            model_list.append(f_info)
        elif stat.S_ISDIR(fstat.st_mode):
            model_list = traverse_all_files(fname, model_list)
    return model_list


def get_all_models(sort_by, filter_by, path):
    res = OrderedDict()
    fileinfos = traverse_all_files(path, [])
    filter_by = filter_by.strip(" ")
    if len(filter_by) != 0:
        fileinfos = [x for x in fileinfos if filter_by.lower()
                     in os.path.basename(x[0]).lower()]
    if sort_by == "name":
        fileinfos = sorted(fileinfos, key=lambda x: os.path.basename(x[0]))
    elif sort_by == "date":
        fileinfos = sorted(fileinfos, key=lambda x: -x[1].st_mtime)
    elif sort_by == "path name":
        fileinfos = sorted(fileinfos)

    for finfo in fileinfos:
        filename = finfo[0]
        name = os.path.splitext(os.path.basename(filename))[0]
        # Prevent a hypothetical "None.pt" from being listed.
        if name != "None":
            res[name + f" [{sd_models.model_hash(filename)}]"] = filename

    return res


def update_cn_models():
    cn_models.clear()
    ext_dirs = (shared.opts.data.get("control_net_models_path", None), getattr(shared.cmd_opts, 'controlnet_dir', None))
    extra_lora_paths = (extra_lora_path for extra_lora_path in ext_dirs
                if extra_lora_path is not None and os.path.exists(extra_lora_path))
    paths = [cn_models_dir, cn_models_dir_old, *extra_lora_paths]

    for path in paths:
        sort_by = shared.opts.data.get(
            "control_net_models_sort_models_by", "name")
        filter_by = shared.opts.data.get("control_net_models_name_filter", "")
        found = get_all_models(sort_by, filter_by, path)
        cn_models.update({**found, **cn_models})

    # insert "None" at the beginning of `cn_models` in-place
    cn_models_copy = OrderedDict(cn_models)
    cn_models.clear()
    cn_models.update({**{"None": None}, **cn_models_copy})

    cn_models_names.clear()
    for name_and_hash, filename in cn_models.items():
        if filename is None:
            continue
        name = os.path.splitext(os.path.basename(filename))[0].lower()
        cn_models_names[name] = name_and_hash

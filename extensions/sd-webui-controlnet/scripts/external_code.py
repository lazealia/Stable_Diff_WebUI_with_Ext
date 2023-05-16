from enum import Enum
from typing import List, Any, Optional, Union, Tuple, Dict
import numpy as np
from modules import scripts, processing, shared
from scripts import global_state
from scripts.processor import preprocessor_sliders_config

from modules.api import api


def get_api_version() -> int:
    return 2


class ControlMode(Enum):
    """
    The improved guess mode.
    """

    BALANCED = "Balanced"
    PROMPT = "My prompt is more important"
    CONTROL = "ControlNet is more important"


class ResizeMode(Enum):
    """
    Resize modes for ControlNet input images.
    """

    RESIZE = "Just Resize"
    INNER_FIT = "Crop and Resize"
    OUTER_FIT = "Resize and Fill"


resize_mode_aliases = {
    'Inner Fit (Scale to Fit)': 'Crop and Resize',
    'Outer Fit (Shrink to Fit)': 'Resize and Fill',
    'Scale to Fit (Inner Fit)': 'Crop and Resize',
    'Envelope (Outer Fit)': 'Resize and Fill',
}


def resize_mode_from_value(value: Union[str, int, ResizeMode]) -> ResizeMode:
    if isinstance(value, str):
        return ResizeMode(resize_mode_aliases.get(value, value))
    elif isinstance(value, int):
        return [e for e in ResizeMode][value]
    else:
        return value


def control_mode_from_value(value: Union[str, int, ControlMode]) -> ControlMode:
    if isinstance(value, str):
        return ControlMode(value)
    elif isinstance(value, int):
        return [e for e in ControlMode][value]
    else:
        return value


InputImage = Union[np.ndarray, str]
InputImage = Union[Dict[str, InputImage], Tuple[InputImage, InputImage], InputImage]


class ControlNetUnit:
    """
    Represents an entire ControlNet processing unit.
    """

    def __init__(
        self,
        enabled: bool=True,
        module: Optional[str]=None,
        model: Optional[str]=None,
        weight: float=1.0,
        image: Optional[InputImage]=None,
        resize_mode: Union[ResizeMode, int, str] = ResizeMode.INNER_FIT,
        low_vram: bool=False,
        processor_res: int=512,
        threshold_a: float=64,
        threshold_b: float=64,
        guidance_start: float=0.0,
        guidance_end: float=1.0,
        pixel_perfect: bool=False,
        control_mode: Union[ControlMode, int, str] = ControlMode.BALANCED,
        **_kwargs,
    ):
        self.enabled = enabled
        self.module = module
        self.model = model
        self.weight = weight
        self.image = image
        self.resize_mode = resize_mode
        self.low_vram = low_vram
        self.processor_res = processor_res
        self.threshold_a = threshold_a
        self.threshold_b = threshold_b
        self.guidance_start = guidance_start
        self.guidance_end = guidance_end
        self.pixel_perfect = pixel_perfect
        self.control_mode = control_mode

    def __eq__(self, other):
        if not isinstance(other, ControlNetUnit):
            return False

        return vars(self) == vars(other)


def to_base64_nparray(encoding: str):
    """
    Convert a base64 image into the image type the extension uses
    """

    return np.array(api.decode_base64_to_image(encoding)).astype('uint8')


def get_all_units_in_processing(p: processing.StableDiffusionProcessing) -> List[ControlNetUnit]:
    """
    Fetch ControlNet processing units from a StableDiffusionProcessing.
    """

    return get_all_units(p.scripts, p.script_args)


def get_all_units(script_runner: scripts.ScriptRunner, script_args: List[Any]) -> List[ControlNetUnit]:
    """
    Fetch ControlNet processing units from an existing script runner.
    Use this function to fetch units from the list of all scripts arguments.
    """

    cn_script = find_cn_script(script_runner)
    if cn_script:
        return get_all_units_from(script_args[cn_script.args_from:cn_script.args_to])

    return []


def get_all_units_from(script_args: List[Any]) -> List[ControlNetUnit]:
    """
    Fetch ControlNet processing units from ControlNet script arguments.
    Use `external_code.get_all_units` to fetch units from the list of all scripts arguments.
    """

    units = []
    i = 0
    while i < len(script_args):
        if script_args[i] is not None:
            units.append(to_processing_unit(script_args[i]))
        i += 1

    return units


def get_single_unit_from(script_args: List[Any], index: int=0) -> Optional[ControlNetUnit]:
    """
    Fetch a single ControlNet processing unit from ControlNet script arguments.
    The list must not contain script positional arguments. It must only contain processing units.
    """

    i = 0
    while i < len(script_args) and index >= 0:
        if index == 0 and script_args[i] is not None:
            return to_processing_unit(script_args[i])
        i += 1

        index -= 1

    return None


def to_processing_unit(unit: Union[Dict[str, Any], ControlNetUnit]) -> ControlNetUnit:
    """
    Convert different types to processing unit.
    If `unit` is a dict, alternative keys are supported. See `ext_compat_keys` in implementation for details.
    """

    ext_compat_keys = {
        'guessmode': 'guess_mode',
        'guidance': 'guidance_end',
        'lowvram': 'low_vram',
        'input_image': 'image'
    }

    if isinstance(unit, dict):
        unit = {ext_compat_keys.get(k, k): v for k, v in unit.items()}

        mask = None
        if 'mask' in unit:
            mask = unit['mask']
            del unit['mask']

        if 'image' in unit and not isinstance(unit['image'], dict):
            unit['image'] = {'image': unit['image'], 'mask': mask} if mask is not None else unit['image'] if unit['image'] else None

        if 'guess_mode' in unit:
            print('Guess Mode is removed since 1.1.136. Please use Control Mode instead.')

        unit = ControlNetUnit(**unit)

    # temporary, check #602
    #assert isinstance(unit, ControlNetUnit), f'bad argument to controlnet extension: {unit}\nexpected Union[dict[str, Any], ControlNetUnit]'
    return unit


def update_cn_script_in_processing(
    p: processing.StableDiffusionProcessing,
    cn_units: List[ControlNetUnit],
    **_kwargs, # for backwards compatibility
):
    """
    Update the arguments of the ControlNet script in `p.script_args` in place, reading from `cn_units`.
    `cn_units` and its elements are not modified. You can call this function repeatedly, as many times as you want.

    Does not update `p.script_args` if any of the folling is true:
    - ControlNet is not present in `p.scripts`
    - `p.script_args` is not filled with script arguments for scripts that are processed before ControlNet
    """

    cn_units_type = type(cn_units) if type(cn_units) in (list, tuple) else list
    script_args = list(p.script_args)
    update_cn_script_in_place(p.scripts, script_args, cn_units)
    p.script_args = cn_units_type(script_args)


def update_cn_script_in_place(
    script_runner: scripts.ScriptRunner,
    script_args: List[Any],
    cn_units: List[ControlNetUnit],
    **_kwargs, # for backwards compatibility
):
    """
    Update the arguments of the ControlNet script in `script_args` in place, reading from `cn_units`.
    `cn_units` and its elements are not modified. You can call this function repeatedly, as many times as you want.

    Does not update `script_args` if any of the folling is true:
    - ControlNet is not present in `script_runner`
    - `script_args` is not filled with script arguments for scripts that are processed before ControlNet
    """

    cn_script = find_cn_script(script_runner)
    if cn_script is None or len(script_args) < cn_script.args_from:
        return

    # fill in remaining parameters to satisfy max models, just in case script needs it.
    max_models = shared.opts.data.get("control_net_max_models_num", 2)
    cn_units = cn_units + [ControlNetUnit(enabled=False)] * max(max_models - len(cn_units), 0)

    cn_script_args_diff = 0
    for script in script_runner.alwayson_scripts:
        if script is cn_script:
            cn_script_args_diff = len(cn_units) - (cn_script.args_to - cn_script.args_from)
            script_args[script.args_from:script.args_to] = cn_units
            script.args_to = script.args_from + len(cn_units)
        else:
            script.args_from += cn_script_args_diff
            script.args_to += cn_script_args_diff


def get_models(update: bool=False) -> List[str]:
    """
    Fetch the list of available models.
    Each value is a valid candidate of `ControlNetUnit.model`.

    Keyword arguments:
    update -- Whether to refresh the list from disk. (default False)
    """

    if update:
        global_state.update_cn_models()

    return list(global_state.cn_models_names.values())


def get_modules(alias_names: bool = False) -> List[str]:
    """
    Fetch the list of available preprocessors.
    Each value is a valid candidate of `ControlNetUnit.module`.

    Keyword arguments:
    alias_names -- Whether to get the ui alias names instead of internal keys
    """

    modules = list(global_state.cn_preprocessor_modules.keys())

    if alias_names:
        modules = [global_state.preprocessor_aliases.get(module, module) for module in modules]

    return modules


def get_modules_detail(alias_names: bool = False) -> Dict[str, Any]:
    """
    get the detail of all preprocessors including
    sliders: the slider config in Auto1111 webUI

    Keyword arguments:
    alias_names -- Whether to get the module detail with alias names instead of internal keys
    """

    _module_detail = {}
    _module_list = get_modules(False)
    _module_list_alias = get_modules(True)
    
    _output_list = _module_list if not alias_names else _module_list_alias
    for index, module in enumerate(_output_list):
        if _module_list[index] in preprocessor_sliders_config:
            _module_detail[module] = {
                "sliders": preprocessor_sliders_config[_module_list[index]]
            }
        else:
            _module_detail[module] = {
                "sliders": []
            }
            
    return _module_detail


def find_cn_script(script_runner: scripts.ScriptRunner) -> Optional[scripts.Script]:
    """
    Find the ControlNet script in `script_runner`. Returns `None` if `script_runner` does not contain a ControlNet script.
    """

    if script_runner is None:
        return None

    for script in script_runner.alwayson_scripts:
        if is_cn_script(script):
            return script


def is_cn_script(script: scripts.Script) -> bool:
    """
    Determine whether `script` is a ControlNet script.
    """

    return script.title().lower() == 'controlnet'

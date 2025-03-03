import unittest
from parameterized import parameterized
import torch
from auto_gptq.utils.import_utils import dynamically_import_QuantLinear

from auto_gptq.nn_modules.qlinear.qlinear_exllama import QuantLinear
from auto_gptq.nn_modules.qlinear.qlinear_marlin import QuantLinear as MarlinQuantLinear

try:
    from exllama_kernels import prepare_buffers, set_tuning_params
except ImportError as e:
    print(f"[WARNING] Could not load exllama_kernels: {e}")

from auto_gptq import AutoGPTQForCausalLM, exllama_set_max_input_length
from auto_gptq.modeling._utils import autogptq_post_init
from auto_gptq.modeling._const import EXLLAMA_DEFAULT_MAX_INPUT_LENGTH

from transformers import AutoTokenizer

def get_diff(a, ref):
    eps = 1e-6
    return f"Maxdiff: {(a - ref).abs().max()}, Mean relative diff: {((a - ref).abs() / (ref.abs() + eps)).mean()}"

CUDA_OLD_REFERENCE = torch.Tensor([5.8398, 6.8555, 7.2734, 6.4219, 6.2070, 5.8203, 6.5664, 6.4219, 6.2148,
    5.3281, 5.7578, 7.5312, 8.1016, 6.1133, 7.2031, 6.6484, 6.5156, 6.0117,
    6.0312, 6.1914, 6.2109, 6.8125, 5.8125, 7.1172, 7.3125, 6.7305, 5.9961,
    6.5117, 6.1914, 5.9648, 7.1680, 6.4766, 7.2070, 6.5469, 6.7734, 6.4219,
    6.8086, 7.0469, 5.9297, 6.4727, 6.2539, 5.9570, 7.2383, 5.8945, 6.0820,
    5.7969, 7.1094, 6.2188, 6.7500, 7.3555, 6.2930, 6.7734, 5.9219, 7.4805,
    6.8750, 6.4102, 6.5898, 6.5469, 7.6016, 6.7461, 5.9492, 7.2227, 5.8164,
    5.4570, 6.2930, 7.3984, 6.0938, 7.3984, 5.9609, 6.3516, 6.5664, 5.7969,
    7.1250, 6.0781, 6.7930, 5.9492, 6.1641, 6.5898, 6.0586, 6.3359, 6.7930,
    7.0469, 6.0664, 6.3320, 5.4414, 6.7617, 5.1641, 7.2891, 6.8516, 6.5312,
    5.6914, 7.3711, 6.8203, 5.9492, 7.0781, 6.3164, 7.1992, 7.1133, 7.4219,
    7.5586, 7.1836, 6.9102, 6.4844, 6.9805, 6.1953, 6.5156, 5.4844, 6.6602,
    6.6719, 7.9844, 6.4727, 6.6367, 6.2227, 6.4531, 5.0625, 6.4609, 6.7031,
    6.6445, 6.5234, 6.8633, 6.6055, 5.6055, 6.4453, 7.2617, 6.3945, 6.6367,
    6.1055, 7.0664, 6.0820, 6.6875, 6.1445, 6.8672, 6.2070, 6.8828, 6.1484,
    6.7070, 6.8516, 6.2734, 7.1055, 7.0586, 6.9648, 5.9727, 6.1016, 6.8750,
    7.0078, 7.1523, 5.7383, 5.9531, 6.5508, 7.5352, 6.1602, 6.2578, 6.3906,
    5.7383, 6.7031, 5.7344, 6.3516, 5.2852, 7.5312, 6.4531, 6.6406, 6.2266,
    6.1094, 5.9102, 5.7617, 6.3789, 7.0508, 6.3750, 6.3320, 6.8555, 6.7266,
    7.0352, 7.7695, 6.3984, 6.5039, 6.8320, 6.1602, 6.0312, 6.3828, 6.9023,
    7.4336, 7.3711, 6.1016, 7.0703, 6.3281, 6.8281, 6.4922, 5.9453, 5.1016,
    6.7188, 6.1406, 6.6289, 7.2695, 6.2070, 6.7070, 7.2930, 7.1836, 6.3828,
    6.1992, 6.7070, 7.8008, 7.7773, 5.6602, 7.0273, 6.6172, 6.0898, 5.3516,
    7.3359, 5.9727, 6.0078, 7.0586, 6.3086, 6.8555, 7.2617, 7.3477, 6.3828,
    7.1133, 6.6328, 7.3516, 6.9141, 7.2031, 6.9805, 6.1719, 6.7812, 8.3047,
    6.5898, 6.3633, 6.2539, 7.2773, 6.5938, 6.4141, 6.8203, 6.8906, 7.8828,
    5.9609, 6.4180, 7.3984, 5.7539, 7.1758, 6.6641, 6.9062, 6.2578, 7.5508,
    6.1719, 6.5742, 5.9375, 6.7891, 6.2109, 6.5039, 6.8750, 6.2031, 6.8828,
    7.1094, 5.9570, 7.2969, 6.6797, 6.8828, 5.5430, 6.9648, 5.8398, 6.5430,
    6.3945, 6.5664, 5.8086, 6.6172, 7.0586, 6.8867, 6.0820, 5.8125, 6.7070,
    7.5742, 6.2578, 6.1328, 6.5391, 5.4531, 6.8242, 6.6953, 6.8008, 6.3398,
    6.4805, 7.2266, 6.3281, 6.6875, 6.4688, 5.9414, 7.4297, 5.8711, 6.0625,
    5.8750, 6.5664, 5.8867, 6.3477, 6.1133, 6.9453, 5.0547, 6.7812, 6.4922,
    7.2422, 5.4688, 6.2109, 7.2148, 6.1758, 5.9297, 7.1953, 5.5195, 6.3203,
    5.9961, 7.9297, 6.2695, 6.4414, 6.7266, 7.1875, 7.3203, 5.4062, 6.0625,
    7.0898, 5.3828, 5.6133, 6.0742, 6.6836, 5.7109, 7.2852, 7.7539, 7.5820,
    6.4258, 5.9336, 6.3750, 6.3555, 7.5469, 6.2539, 6.5898, 6.4102, 7.0469,
    5.7344, 7.2031, 6.7969, 5.6836, 7.6523, 6.9297, 7.8672, 6.4766, 6.3008,
    7.0977, 6.5430, 7.0938, 5.8398, 6.9883, 6.5312, 6.3203, 6.3594, 5.4062,
    6.9688, 5.7930, 6.3164, 6.5547, 7.1992, 5.8750, 6.3008, 6.7930, 6.0391,
    7.4766, 6.6094, 6.5625, 5.9805, 6.2422, 7.2109, 6.6875, 5.3047, 7.6211,
    5.9453, 6.5625, 6.1641, 6.1250, 6.5977, 7.7422, 7.0742, 5.6875, 6.2656,
    6.6250, 6.8945, 5.7070, 6.3203, 5.7500, 6.2695, 6.2773, 6.8516, 6.4883,
    7.0000, 6.7578, 6.1875, 5.9844, 5.5703, 6.7188, 5.5273, 5.3438, 7.2500,
    6.7852, 6.5195, 6.8125, 6.0664, 6.7852, 7.0000, 7.0781, 6.8477, 7.2930,
    6.3438, 7.1523, 6.3281, 6.8047, 7.3203, 5.3359, 6.1484, 6.5586, 7.3828,
    6.2344, 7.1523, 6.4102, 5.5898, 7.0195, 7.1172, 5.8008, 6.5742, 6.2891,
    8.0312, 6.9023, 6.5898, 7.1953, 6.7266, 6.0078, 5.5430, 6.4766, 6.4258,
    5.9648, 8.0859, 5.0547, 7.2188, 7.4375, 6.5156, 5.9922, 6.3281, 6.2852,
    6.7734, 6.2461, 6.9805, 5.4648, 5.8867, 6.8242, 6.3008, 6.3281, 7.3047,
    7.1836, 6.5195, 6.6328, 6.7188, 5.4336, 6.5078, 5.3477, 5.5508, 7.3125,
    5.8750, 6.5195, 6.2383, 6.3594, 6.0898, 6.4141, 5.9844, 6.6250, 7.7109,
    6.0391, 7.2344, 5.9453, 5.9453, 7.0586, 5.6641, 7.2773, 6.5195, 7.2227,
    6.3359, 5.3203, 6.4375, 7.2383, 6.4023, 6.2148, 7.3750, 5.8164, 6.2109,
    6.5430, 5.8164, 6.1680, 6.7656, 6.0820, 6.1094, 6.5312, 6.8906, 6.8320,
    6.1289, 6.3125, 7.6797, 6.3008, 6.0000, 7.3320, 6.7852, 6.9297, 6.6328,
    6.2266, 5.1602, 6.2031, 7.0547, 5.9492, 6.0703, 6.0977, 6.8086, 6.0742,
    6.0195, 7.0625, 6.5781, 5.7461, 6.1562, 7.0430, 6.7148, 6.5312, 6.5820,
    6.4570, 7.5508, 5.6289, 6.0547, 6.5000, 7.3125, 5.8477, 5.9297, 6.2578,
    6.0078, 5.9922, 7.3398, 7.4922, 7.8906, 7.5547, 5.4648, 6.5156, 6.3242,
    6.1094, 6.9219, 6.7227, 6.6836, 7.4023, 5.9648, 7.2383, 6.7695, 6.6797,
    7.0547, 6.3047, 6.4688, 6.9961, 6.0391, 5.9727, 6.8398, 6.7422, 5.7656,
    5.4766, 6.7852, 7.0820, 5.3516, 7.6523, 5.1562, 6.6445, 6.1211, 6.2695,
    6.0703, 6.3594, 6.4062, 6.3398, 5.7578, 6.5391, 6.2500, 6.5742, 6.5000,
    7.5625, 7.0117, 6.5547, 7.1250, 6.4453, 6.6094, 6.1875, 6.4219, 6.6172,
    6.4336, 6.5703, 6.1758, 6.4219, 6.6016, 6.7383, 6.7070, 6.1328, 5.5586,
    6.6367, 6.3789, 6.2578, 5.5039, 6.6172, 6.4648, 5.8086, 7.2031, 5.8125,
    6.3711, 7.6758, 7.1289, 5.8086, 6.3008, 6.2109, 6.1602, 6.1797, 7.2305,
    6.7266, 6.2422, 5.6719, 6.7070, 6.9414, 6.8594, 7.4023, 7.2109, 6.0156,
    6.6680, 6.6172, 7.1250, 6.6523, 6.9531, 6.7617, 6.4961, 6.9414, 5.7188,
    7.6367, 6.5469, 6.2305, 6.4414, 7.4648, 5.9102, 6.2461, 6.1367, 6.8203,
    6.5703, 6.8867, 7.0000, 6.7539, 6.1719, 6.5469, 6.2422, 5.4297, 5.7305,
    5.1641, 6.1875, 7.0312, 6.6484, 6.0234, 7.4102, 6.8711, 6.3086, 6.3711,
    6.7344, 6.6992, 5.9766, 7.3906, 7.1875, 6.4883, 6.3984, 7.3438, 6.9688,
    6.9062, 6.4375, 6.7891, 7.0117, 6.4883, 5.7500, 7.0898, 7.0742, 6.7070,
    5.8750, 6.0469, 6.6445, 5.2773, 6.8984, 6.1641, 7.0508, 7.4609, 5.0273,
    6.7734, 6.4531, 5.7656, 6.5312, 7.4648, 6.1250, 6.5625, 7.1367, 6.0625,
    6.1211, 6.9766, 6.6758, 6.3164, 6.8828, 6.8203, 6.7500, 6.5352, 7.3008,
    6.7852, 6.1914, 5.0508, 6.7188, 7.1172, 6.8008, 6.8086, 5.4883, 6.9180,
    6.5742, 6.1719, 7.0469, 7.1523, 5.9492, 5.8594, 6.8320, 6.1719, 6.2031,
    6.8398, 7.3008, 6.6289, 6.4922, 6.0000, 5.4766, 6.3320, 6.5117, 6.2812,
    7.5742, 6.3516, 7.0039, 6.4570, 7.1523, 7.6289, 6.2578, 7.1875, 6.4844,
    5.7930, 6.7070, 7.5508, 7.1797, 6.0430, 6.8711, 6.5742, 7.5781, 6.4766,
    6.5391, 6.9453, 6.1992, 6.6367, 6.2812, 6.0234, 6.6953, 7.0312, 6.2031,
    6.5625, 6.6719, 6.1719, 6.5586, 5.7031, 7.4609, 6.6211, 7.7227, 6.9141,
    6.0469, 6.2500, 5.3828, 6.0078, 5.8164, 5.8867, 6.1523, 6.6523, 6.6953,
    7.3125, 6.4844, 5.9570, 5.9531, 6.2109, 5.5039, 6.5117, 6.8203, 6.6133,
    6.4766, 5.9297, 7.1445, 7.1914, 6.0117, 6.8281, 6.7422, 6.1328, 6.9805,
    6.5625, 6.9180, 7.1133, 7.3359, 5.7617, 5.8711, 6.4961, 6.5859, 6.2422,
    6.5273, 6.7461, 6.6992, 6.7695, 6.6289, 5.9453, 5.9805, 7.1172, 6.6719,
    6.0039, 7.6875, 6.7812, 7.8359, 6.9531, 7.4336, 7.6602, 6.8164, 7.3945,
    7.1602, 6.8789, 5.0078, 6.0547, 6.8086, 6.7070, 6.4688, 6.4492, 6.6172,
    5.5625, 6.6914, 6.4297, 5.7461, 5.3359, 6.8750, 6.4609, 7.4062, 5.2070,
    6.0820, 6.7383, 6.5703, 6.1797, 6.7070, 6.5977, 5.9961, 6.6328, 6.9375,
    6.3906, 6.6484, 4.9609, 6.6445, 6.5898, 7.1875, 7.5195, 6.7969, 6.1367,
    6.8906, 7.4297, 6.3633, 6.0508, 6.5000, 6.4648, 6.7539, 6.7109, 5.8086,
    6.6016, 7.1133, 4.8672, 6.6367, 6.1641, 5.1758, 6.9453, 6.3242, 7.0664,
    6.4805, 6.3516, 6.7383, 8.4688, 6.7305, 5.9844, 6.5938, 7.2969, 6.5977,
    7.5898, 6.2969, 6.8672, 6.6680, 7.1289, 6.6875, 5.4258, 8.1875, 8.0391,
    7.7969, 6.6445, 7.0703, 7.3359, 6.9805, 6.6328, 6.5352, 6.2422, 5.5820,
    6.8633, 6.8047, 6.5703, 6.0117, 6.7539, 7.1719, 6.8438, 7.3633, 6.6016,
    7.2070, 6.4727, 5.8008, 7.4062, 7.4805, 6.6445, 5.9023, 6.3984, 6.9961,
    6.6680, 6.8242, 6.7148, 6.6172, 6.9727, 6.8320, 5.9766, 6.6133, 5.5977,
    6.7773, 7.3906, 6.9219, 7.0781, 6.6914, 5.7539, 6.7969, 6.8008, 5.8047,
    7.1055, 6.4961, 6.0352, 5.6211, 7.4414, 7.0703, 6.1172, 6.7461, 6.4492,
    7.7148, 6.4258, 6.0039, 6.5156, 7.2188, 7.4531, 7.4844, 7.5938, 7.4023,
    6.7617, 6.0078, 6.3320, 5.8906, 7.5977, 5.6523, 6.7734, 6.3008, 5.2227,
    7.1719, 7.1289, 6.6602, 5.4609, 7.0312, 6.0820, 6.1719, 6.0000, 6.5547,
    6.6328, 7.0547, 7.0859, 6.2656, 5.5234, 6.0273, 6.7891, 7.1875, 6.9531,
    6.8203, 6.3516, 6.1172, 6.4648, 6.9180, 7.3906, 6.2812, 5.7109, 6.1484,
    6.9102, 6.8711, 7.0156, 6.1445, 5.8867, 6.3828, 5.9961, 6.6914, 6.7891,
    7.0820, 6.6719, 6.9297, 6.3750, 6.7578, 6.4883, 6.2227, 6.2305, 6.0508,
    6.6484, 5.7578, 7.2070, 7.2383, 6.9375, 7.2578, 6.5312, 6.0312, 6.7930,
    6.2578, 7.0625, 7.2148, 6.4961, 7.0703, 6.4727, 7.3906]).to(torch.float16)

class TestsQ4Exllama(unittest.TestCase):
    def test_exllama(self):

        group_size = 128

        m = 1
        k = 1024
        n = 1024
        device = torch.device("cuda:0")

        linear_class = dynamically_import_QuantLinear(use_triton=False, desc_act=False, group_size=group_size, bits=4, disable_exllama=False, disable_exllamav2=True)

        linear = linear_class(
            bits=4,
            group_size=group_size,
            infeatures=k,
            outfeatures=n,
            bias=False,
        )
        self.assertTrue(isinstance(linear, QuantLinear))

        torch.manual_seed(42)

        linear.qweight = torch.randint(-100, 100, size=linear.qweight.shape, dtype=torch.int32)
        linear.scales = linear.scales + 0.002

        linear = linear.eval()
        linear = linear.to(device)

        linear = autogptq_post_init(linear, use_act_order=False)

        max_inner_outer_dim = max(k, n)
        max_dq_buffer_size = linear.infeatures * linear.outfeatures
        max_input_len = 2048
        buffers = {
            "temp_state": torch.zeros((max_input_len, max_inner_outer_dim), dtype=torch.float16, device=device),
            "temp_dq": torch.zeros((1, max_dq_buffer_size), dtype=torch.float16, device=device)
        }

        prepare_buffers(device, buffers["temp_state"], buffers["temp_dq"])

        # Using the default from exllama repo here.
        matmul_recons_thd = 8
        matmul_fused_remap = False
        matmul_no_half2 = False
        set_tuning_params(matmul_recons_thd, matmul_fused_remap, matmul_no_half2)

        inp = torch.rand(1, m, k, dtype=torch.float16).to(device)

        with torch.no_grad():
            res = linear(inp)[0][0]

        reference = CUDA_OLD_REFERENCE.to(device)

        self.assertTrue(torch.allclose(res, reference, rtol=3e-5, atol=2e-2), get_diff(res, reference))
    
    def test_exllama_buffer_size(self):
        prompt = "I am in Paris and" * 450
        device = torch.device("cuda:0")

        model_id = "TheBloke/vicuna-13B-1.1-GPTQ-4bit-128g"
        revision = "actorder"
        model_basename = "vicuna-13B-1.1-GPTQ-4bit-128g.latest"

        model_q = AutoGPTQForCausalLM.from_quantized(model_id, revision=revision, device="cuda:0", use_triton=False, inject_fused_attention=False, inject_fused_mlp=True, model_basename=model_basename, disable_exllama=False, disable_exllamav2=True)
        tokenizer = AutoTokenizer.from_pretrained(model_id)

        inp = tokenizer(prompt, return_tensors="pt").to(device)

        self.assertTrue(inp["input_ids"].shape[1] > EXLLAMA_DEFAULT_MAX_INPUT_LENGTH)  # 2048 is the default max_input_length

        with self.assertRaises(RuntimeError) as cm:
            res = model_q.generate(**inp, num_beams=1, min_new_tokens=3, max_new_tokens=3)
        self.assertTrue("temp_state buffer is too small" in str(cm.exception))

        model_q = exllama_set_max_input_length(model_q, 4096)

        res = model_q.generate(**inp, num_beams=1, min_new_tokens=3, max_new_tokens=3)

        model_q = exllama_set_max_input_length(model_q, 1034)

        with self.assertRaises(RuntimeError) as cm:
            res = model_q.generate(**inp, num_beams=1, min_new_tokens=3, max_new_tokens=3)
        self.assertTrue("temp_state buffer is too small" in str(cm.exception))

    def test_generation_no_act_order(self):
        prompt = "I am in Paris and"
        device = torch.device("cuda:0")

        # Reference generated with the cuda-old kernel
        reference_output = "<s> I am in Paris and I am going to the Louvre Museum. What time does it open and what is the best way to get there?\nThe Louvre Museum in Paris is open from 9:00 AM to 6:00 PM every day except for Tuesdays. The best way to get"

        model_id = "TheBloke/WizardLM-7B-uncensored-GPTQ"
        model_q = AutoGPTQForCausalLM.from_quantized(model_id, device="cuda:0", use_triton=False, inject_fused_attention=True, inject_fused_mlp=True, disable_exllama=False, disable_exllamav2=True)
        tokenizer = AutoTokenizer.from_pretrained(model_id)

        inp = tokenizer(prompt, return_tensors="pt").to(device)

        res = model_q.generate(**inp, num_beams=1, min_new_tokens=60, max_new_tokens=60)

        predicted_text = tokenizer.decode(res[0])

        self.assertEqual(predicted_text, reference_output)

    def test_generation_with_act_order(self):
        prompt = "I am in Paris and"
        device = torch.device("cuda:0")

        # Reference generated with the cuda-old kernel
        reference_output = "<s> I am in Paris and it is a beautiful day. I am sitting in a café, drinking coffee and writing this book. I am surrounded by the sights and sounds of the city, and I am filled with a sense of contentment and gratitude.\n\nI am grateful for the opportunity to live and"

        model_id = "TheBloke/vicuna-13B-1.1-GPTQ-4bit-128g"
        revision = "actorder"
        model_basename = "vicuna-13B-1.1-GPTQ-4bit-128g.latest"

        model_q = AutoGPTQForCausalLM.from_quantized(model_id, revision=revision, device="cuda:0", use_triton=False, inject_fused_attention=False, inject_fused_mlp=True, model_basename=model_basename, disable_exllama=False, disable_exllamav2=True)
        tokenizer = AutoTokenizer.from_pretrained(model_id)

        inp = tokenizer(prompt, return_tensors="pt").to(device)

        res = model_q.generate(**inp, num_beams=1, min_new_tokens=60, max_new_tokens=60)

        predicted_text = tokenizer.decode(res[0])

        self.assertEqual(predicted_text, reference_output)

    def test_multigpu(self):
        # TODO
        pass


class TestsQ4CUDA(unittest.TestCase):
    REFERENCE_OLD_HALF = torch.Tensor([1.5332, 2.1250, 1.7910, 1.8008, 1.9688, 1.3262, 1.7627, 1.8164, 1.9307,
            1.8574, 1.5449, 1.5293, 1.6074, 1.5566, 1.8545, 1.6582, 1.8838, 2.0215,
            1.8525, 1.2920, 1.9561, 2.2617, 1.7891, 2.2656, 1.6543, 2.0566, 1.4756,
            1.1826, 1.8174, 2.1191, 1.6641, 2.0586, 1.6182, 1.7627, 1.7920, 1.4424,
            2.0723, 1.6865, 1.2979, 2.0840, 1.6729, 1.9648, 2.1602, 1.6006, 1.2773,
            2.2129, 1.8057, 1.7285, 1.6621, 1.6475, 1.4805, 1.7959, 1.5010, 0.8643,
            2.6680, 2.0918, 1.8555, 1.9795, 1.3271, 1.8359, 1.6338, 1.9766, 1.7881,
            1.6025, 1.7637, 1.7012, 1.7852, 1.5674, 0.8091, 1.7188, 1.6123, 1.8525,
            1.4434, 1.9590, 1.5801, 1.4209, 1.7178, 1.8408, 2.4141, 1.9658, 1.4922,
            2.1992, 1.9473, 1.8047, 1.2979, 1.6396, 1.6221, 1.5020, 1.9941, 1.7725,
            1.6064, 1.5449, 1.8418, 1.2656, 1.4824, 1.7734, 2.0098, 1.7197, 1.7686,
            1.4160, 1.7275, 2.1738, 1.9609, 1.7686, 1.6396, 2.1465, 1.2188, 1.2002,
            2.1113, 1.7227, 1.5811, 1.7607, 2.2773, 1.8945, 1.4111, 1.5801, 1.7744,
            2.0684, 2.1621, 1.8027, 1.1045, 1.9648, 2.2402, 2.0742, 1.3330, 1.5840,
            2.1465, 2.0176, 1.5068, 1.9834, 1.7725, 1.5527, 1.7803, 1.7744, 1.5312,
            1.2695, 1.9209, 2.0469, 1.6777, 2.5215, 1.8389, 1.7598, 1.5498, 1.6807,
            1.7324, 1.5938, 1.9268, 1.7734, 1.4463, 2.0391, 2.0527, 2.2129, 1.6787,
            2.0586, 1.8975, 1.5713, 1.6992, 1.8770, 1.7207, 1.7080, 1.1611, 1.8584,
            2.4570, 1.6016, 1.4834, 1.1777, 1.7969, 1.8955, 1.8906, 1.6738, 1.7510,
            1.4316, 1.8340, 2.2461, 1.7744, 2.1934, 1.4824, 1.8828, 1.6387, 2.4629,
            1.8887, 1.5137, 1.4648, 1.6406, 1.7188, 2.2656, 1.5801, 2.1484, 2.0625,
            2.0098, 1.7549, 1.1768, 1.4385, 2.0723, 1.6172, 1.7832, 1.8301, 1.6064,
            1.5215, 1.9297, 2.3750, 2.1504, 1.7070, 1.1289, 1.4473, 1.5674, 1.6836,
            2.2930, 1.1221, 1.5557, 1.7559, 1.8281, 2.0703, 1.9443, 2.0684, 2.2988,
            1.6348, 2.3379, 2.4414, 1.8857, 2.0039, 1.4844, 1.5488, 1.6514, 2.3711,
            1.9941, 2.3066, 1.4287, 2.1777, 1.6445, 1.6025, 1.5938, 1.5508, 1.9502,
            2.1309, 1.2666, 1.1523, 1.9561, 1.8584, 1.9746, 1.5986, 1.9688, 2.1973,
            1.1523, 2.3281, 1.2451, 1.8447, 2.2051, 1.5254, 1.5342, 2.1016, 1.6523,
            1.6279, 1.1680, 1.3037, 2.1035]).to(torch.float16)

    REFERENCE_OLD_NO_HALF = torch.Tensor([1.5332, 2.1250, 1.7910, 1.7998, 1.9678, 1.3262, 1.7617, 1.8154, 1.9307,
        1.8574, 1.5449, 1.5293, 1.6074, 1.5557, 1.8545, 1.6582, 1.8838, 2.0195,
        1.8525, 1.2920, 1.9561, 2.2617, 1.7891, 2.2656, 1.6543, 2.0566, 1.4756,
        1.1826, 1.8164, 2.1191, 1.6641, 2.0586, 1.6182, 1.7617, 1.7920, 1.4424,
        2.0723, 1.6865, 1.2969, 2.0840, 1.6729, 1.9639, 2.1602, 1.5996, 1.2773,
        2.2129, 1.8057, 1.7275, 1.6621, 1.6475, 1.4805, 1.7949, 1.5010, 0.8643,
        2.6680, 2.0918, 1.8545, 1.9795, 1.3271, 1.8350, 1.6338, 1.9766, 1.7881,
        1.6025, 1.7637, 1.7012, 1.7842, 1.5664, 0.8086, 1.7188, 1.6113, 1.8516,
        1.4434, 1.9590, 1.5801, 1.4209, 1.7168, 1.8408, 2.4141, 1.9658, 1.4922,
        2.1973, 1.9463, 1.8047, 1.2979, 1.6396, 1.6221, 1.5010, 1.9941, 1.7725,
        1.6064, 1.5449, 1.8418, 1.2656, 1.4824, 1.7734, 2.0098, 1.7188, 1.7686,
        1.4160, 1.7266, 2.1738, 1.9600, 1.7686, 1.6396, 2.1465, 1.2188, 1.2002,
        2.1113, 1.7227, 1.5811, 1.7598, 2.2773, 1.8936, 1.4102, 1.5801, 1.7734,
        2.0684, 2.1621, 1.8027, 1.1045, 1.9648, 2.2402, 2.0742, 1.3330, 1.5840,
        2.1465, 2.0176, 1.5068, 1.9834, 1.7725, 1.5527, 1.7793, 1.7744, 1.5312,
        1.2695, 1.9209, 2.0469, 1.6777, 2.5195, 1.8389, 1.7598, 1.5498, 1.6797,
        1.7324, 1.5928, 1.9258, 1.7734, 1.4463, 2.0391, 2.0508, 2.2129, 1.6787,
        2.0586, 1.8975, 1.5713, 1.6992, 1.8770, 1.7207, 1.7070, 1.1602, 1.8584,
        2.4570, 1.6016, 1.4834, 1.1777, 1.7959, 1.8955, 1.8906, 1.6738, 1.7510,
        1.4316, 1.8330, 2.2461, 1.7744, 2.1934, 1.4824, 1.8828, 1.6387, 2.4629,
        1.8887, 1.5137, 1.4648, 1.6406, 1.7178, 2.2637, 1.5801, 2.1484, 2.0605,
        2.0098, 1.7539, 1.1768, 1.4375, 2.0723, 1.6162, 1.7832, 1.8291, 1.6064,
        1.5215, 1.9297, 2.3750, 2.1504, 1.7061, 1.1289, 1.4473, 1.5674, 1.6836,
        2.2930, 1.1221, 1.5547, 1.7559, 1.8281, 2.0703, 1.9443, 2.0684, 2.2988,
        1.6348, 2.3379, 2.4414, 1.8857, 2.0020, 1.4834, 1.5488, 1.6514, 2.3711,
        1.9941, 2.3047, 1.4277, 2.1777, 1.6445, 1.6025, 1.5938, 1.5508, 1.9502,
        2.1309, 1.2666, 1.1514, 1.9551, 1.8584, 1.9746, 1.5986, 1.9688, 2.1953,
        1.1514, 2.3262, 1.2451, 1.8447, 2.2051, 1.5254, 1.5342, 2.1016, 1.6523,
        1.6279, 1.1680, 1.3037, 2.1035]).to(torch.float16)

    @parameterized.expand([(False,), (True,)])
    def test_cuda_old(self, use_half2: bool):

        group_size = 128

        # test the 256 kernel (in_features % 256 == 0 and out_features % 256 == 0)
        m = 1
        k = 256
        n = 256
        device = "cuda"

        linear_class = dynamically_import_QuantLinear(use_triton=False, desc_act=False, group_size=group_size, bits=4, disable_exllama=True, disable_exllamav2=True)

        weight_dtype = torch.float16 if use_half2 else torch.float32
        linear = linear_class(
            bits=4,
            group_size=group_size,
            infeatures=k,
            outfeatures=n,
            bias=False,
            weight_dtype=weight_dtype
        )

        torch.manual_seed(42)

        linear.qweight = torch.randint(-100, 100, size=linear.qweight.shape, dtype=torch.int32)
        linear.scales = linear.scales + 0.002
        linear.use_cuda_fp16 = use_half2
        self.assertTrue(linear.autogptq_cuda_available)

        # We cast twice just for the seed.
        inp = torch.rand(1, m, k, dtype=torch.float16).to(device).to(weight_dtype)

        linear = linear.eval()
        linear = linear.to(device)

        with torch.no_grad():
            res = linear(inp)[0][0]

        if use_half2:
            reference = self.REFERENCE_OLD_HALF.to(device).to(weight_dtype)
        else:
            reference = self.REFERENCE_OLD_NO_HALF.to(device).to(weight_dtype)

        self.assertTrue(torch.allclose(res, reference, rtol=1e-3), get_diff(res, reference))
    
    @parameterized.expand([
        (torch.float32, "cpu"),
        (torch.float32, "cuda:0"),
        (torch.float16, "cuda:0"),
    ])
    def test_generation_with_act_order(self, torch_dtype, device):
        prompt = "I am in Paris and"

        # Reference generated with the cuda-old kernel
        if device == "cpu":
            # CPU implementation is extremely slow.
            new_tokens = 2
            reference_output = "<s> I am in Paris and it is"
        else:
            reference_output = "<s> I am in Paris and it is a beautiful day. I am sitting in a café, drinking coffee and writing this book. I am surrounded by the sights and sounds of the city, and I am filled with a sense of contentment and gratitude.\n\nI am grateful for the opportunity to live and"
            new_tokens = 60

        model_id = "TheBloke/vicuna-13B-1.1-GPTQ-4bit-128g"
        revision = "actorder"
        model_basename = "vicuna-13B-1.1-GPTQ-4bit-128g.latest"

        model_q = AutoGPTQForCausalLM.from_quantized(model_id, revision=revision, device=device, use_triton=False, inject_fused_attention=False, inject_fused_mlp=True, model_basename=model_basename, disable_exllama=True, disable_exllamav2=True, torch_dtype=torch_dtype)

        tokenizer = AutoTokenizer.from_pretrained(model_id)

        inp = tokenizer(prompt, return_tensors="pt").to(device)

        # This one uses Autocast.
        res = model_q.generate(**inp, num_beams=1, min_new_tokens=new_tokens, max_new_tokens=new_tokens)
        predicted_text = tokenizer.decode(res[0])
        self.assertEqual(predicted_text, reference_output)

        # This one does not.
        res = model_q.model.generate(**inp, num_beams=1, min_new_tokens=new_tokens, max_new_tokens=new_tokens)
        predicted_text = tokenizer.decode(res[0])
        self.assertEqual(predicted_text, reference_output)

    @parameterized.expand([
        (torch.float32, "cpu"),
        (torch.float32, "cuda:0"),
        (torch.float16, "cuda:0"),
    ])
    def test_generation_no_act_order(self, torch_dtype, device):
        prompt = "I am in Paris and"

        # Reference generated with the cuda-old kernel
        if device == "cpu":
            # CPU implementation is extremely slow.
            new_tokens = 3
            reference_output = "<s> I am in Paris and I am going"
        else:
            reference_output = "<s> I am in Paris and I am going to the Louvre Museum. What time does it open and what is the best way to get there?\nThe Louvre Museum in Paris is open from 9:00 AM to 6:00 PM every day except for Tuesdays. The best way to get"
            new_tokens = 60

        model_id = "TheBloke/WizardLM-7B-uncensored-GPTQ"
        
        model_q = AutoGPTQForCausalLM.from_quantized(model_id, device=device, use_triton=False, disable_exllama=True, disable_exllamav2=True, torch_dtype=torch_dtype)
        tokenizer = AutoTokenizer.from_pretrained(model_id)

        inp = tokenizer(prompt, return_tensors="pt").to(device)
        
        # This one uses Autocast.
        res = model_q.generate(**inp, num_beams=1, min_new_tokens=new_tokens, max_new_tokens=new_tokens)
        predicted_text = tokenizer.decode(res[0])
        self.assertEqual(predicted_text, reference_output)

        # This one does not.
        res = model_q.model.generate(**inp, num_beams=1, min_new_tokens=new_tokens, max_new_tokens=new_tokens)
        predicted_text = tokenizer.decode(res[0])
        self.assertEqual(predicted_text, reference_output)

class TestsQ4ExllamaV2(unittest.TestCase):
    def test_exllamav2(self):
        from auto_gptq.nn_modules.qlinear.qlinear_exllamav2 import QuantLinear
        
        group_size = 128

        m = 1
        k = 1024
        n = 1024
        device = torch.device("cuda:0")

        linear_class = dynamically_import_QuantLinear(use_triton=False, desc_act=False, group_size=group_size, bits=4)

        linear = linear_class(
            bits=4,
            group_size=group_size,
            infeatures=k,
            outfeatures=n,
            bias=False,
        )
        
        self.assertTrue(isinstance(linear, QuantLinear))

        torch.manual_seed(42)

        linear.qweight = torch.randint(-100, 100, size=linear.qweight.shape, dtype=torch.int32)
        linear.scales = linear.scales + 0.002

        linear = linear.eval()
        linear = linear.to(device)

        linear = autogptq_post_init(linear, use_act_order=False)

        inp = torch.rand(1, m, k, dtype=torch.float16).to(device)

        with torch.no_grad():
            res = linear(inp)[0][0]

        reference = CUDA_OLD_REFERENCE.to(device)

        self.assertTrue(torch.allclose(res, reference, rtol=3e-5, atol=2e-2), get_diff(res, reference))
    
    def test_generation_no_act_order(self):
        prompt = "I am in Paris and"
        device = torch.device("cuda:0")

        # Reference generated with the cuda-old kernel
        reference_output = "<s> I am in Paris and I am going to the Louvre Museum. What time does it open and what is the best way to get there?\nThe Louvre Museum in Paris is open from 9:00 AM to 6:00 PM every day except for Tuesdays. The best way to get"
        
        model_id = "TheBloke/WizardLM-7B-uncensored-GPTQ"
        
        model_q = AutoGPTQForCausalLM.from_quantized(model_id, device="cuda:0", use_triton=False)
        tokenizer = AutoTokenizer.from_pretrained(model_id)

        inp = tokenizer(prompt, return_tensors="pt").to(device)

        res = model_q.generate(**inp, num_beams=1, do_sample=False, min_new_tokens=60, max_new_tokens=60)

        predicted_text = tokenizer.decode(res[0])
        
        self.assertEqual(predicted_text, reference_output)
        
    def test_generation_with_act_order(self):
        prompt = "I am in Paris and"
        device = torch.device("cuda:0")

        # Reference generated with the cuda-old kernel
        reference_output = "<s> I am in Paris and it is a beautiful day. I am sitting in a café, drinking coffee and writing this book. I am surrounded by the sights and sounds of the city, and I am filled with a sense of contentment and gratitude.\n\nI am grateful for the opportunity to live and"

        model_id = "TheBloke/vicuna-13B-1.1-GPTQ-4bit-128g"
        revision = "actorder"
        model_basename = "vicuna-13B-1.1-GPTQ-4bit-128g.latest"

        model_q = AutoGPTQForCausalLM.from_quantized(model_id, revision=revision, device="cuda:0", use_triton=False, inject_fused_attention=False, inject_fused_mlp=True, model_basename=model_basename)
        tokenizer = AutoTokenizer.from_pretrained(model_id)

        inp = tokenizer(prompt, return_tensors="pt").to(device)

        res = model_q.generate(**inp, num_beams=1, min_new_tokens=60, max_new_tokens=60)

        predicted_text = tokenizer.decode(res[0])

        self.assertEqual(predicted_text, reference_output)

    def test_exllama_v2_buffer_size(self):
        # prompt = "I'm in Paris and" * 450
        prompt = "I'm in Paris and" * 1000
        device = torch.device("cuda:0")

        model_id = "TheBloke/vicuna-13B-1.1-GPTQ-4bit-128g"
        revision = "actorder"
        model_basename = "vicuna-13B-1.1-GPTQ-4bit-128g.latest"

        model_q = AutoGPTQForCausalLM.from_quantized(model_id, revision=revision, device="cuda:0", use_triton=False, inject_fused_attention=True, inject_fused_mlp=True, model_basename=model_basename)
        
        tokenizer = AutoTokenizer.from_pretrained(model_id)

        inp = tokenizer(prompt, return_tensors="pt").to(device)
        
        self.assertTrue(inp["input_ids"].shape[1] > 2048)  # 2048 is the default max_input_length for LLama
        
        res = model_q.generate(**inp, num_beams=1, min_new_tokens=3, max_new_tokens=3)


class TestsMixtral(unittest.TestCase):
    def test_mixtral_generation(self):
        prompt = "I am in Paris and"
        device = torch.device("cuda:0")

        # Reference generated with the cuda-old kernel
        reference_output = '''<s> I am in Paris andpublishedющиеcs performancesension manual offset亡VIDEO Kel RepubliczwDrawlichen LondresPSungspfn CreahooEESlider laughselvesлександTrytpl recallслу Ор coldsubset########serdeacion providestrm thoughts président oktobermulticol../редβ themselvesterraряд conflictscommandMass diagonal選 ptrTY還 Havepliedument relate redu'''

        model_id = "TheBlokeAI/Mixtral-tiny-GPTQ"
        model_basename = "model"

        model_q = AutoGPTQForCausalLM.from_quantized(model_id, use_safetensors=True, device="cuda:0", use_triton=False, inject_fused_attention=False, inject_fused_mlp=False, model_basename=model_basename)
        tokenizer = AutoTokenizer.from_pretrained(model_id)

        inp = tokenizer(prompt, return_tensors="pt").to(device)

        res = model_q.generate(**inp, num_beams=1, min_new_tokens=60, max_new_tokens=60, do_sample=False)

        predicted_text = tokenizer.decode(res[0])

        self.assertEqual(predicted_text, reference_output)


class TestQ4Marlin(unittest.TestCase):
    def test_generation(self):
        # Reference generated with the cuda-old kernel and TheBloke/Llama-2-7B-Chat-GPTQ
        reference_output = "<s> I am in Paris and I am feeling very sad and lonely. everybody I know is busy and I don't have any friends here. I am staying in a small apartment in the 11th arrondissement and I am feeling very isolated. I miss my friends and family back home and I don'"

        prompt = "I am in Paris and"
        device = torch.device("cuda:0")

        model_id = "TheBloke/Llama-2-7B-Chat-GPTQ"
        model_q = AutoGPTQForCausalLM.from_quantized(model_id, device="cuda:0", use_triton=False, inject_fused_attention=False, inject_fused_mlp=False, disable_exllama=True, disable_exllamav2=True, use_marlin=True)

        has_marlin = False
        for name, module in model_q.named_modules():
            if isinstance(module, MarlinQuantLinear):
                has_marlin = True
                break
        self.assertTrue(has_marlin)

        tokenizer = AutoTokenizer.from_pretrained(model_id)

        inp = tokenizer(prompt, return_tensors="pt").to(device)

        res = model_q.generate(**inp, num_beams=1, min_new_tokens=60, max_new_tokens=60)

        predicted_text = tokenizer.decode(res[0])

        self.assertEqual(predicted_text, reference_output)

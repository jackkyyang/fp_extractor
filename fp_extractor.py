"""
MIT License

Copyright (c) 2025 jackkyyang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from collections import namedtuple
import tkinter as tk
from tkinter import font

FPFormat = namedtuple("FPFormat", ["width", "exponent", "mantissa"])
Fp = namedtuple("FP", ["sign", "exponent", "mantissa"])

# Define the Floating-Point Formats
FP_CONFIG = {
    "FP64": FPFormat(64, (62, 52), (51, 0)),
    "FP32": FPFormat(32, (30, 23), (22, 0)),
    "TF32": FPFormat(32, (30, 23), (22, 13)),
    "FP16": FPFormat(16, (14, 10), (9, 0)),
    "BF16": FPFormat(16, (14, 7), (6, 0)),
    "FP8_E4M3": FPFormat(8, (6, 3), (2, 0)),
    "FP8_E5M2": FPFormat(8, (6, 2), (1, 0)),
}


def hex_str_check(hex_str: str) -> bool:
    """Check if the input is a valid hex string"""
    return all(c in "0123456789abcdef" for c in hex_str.lower())


def bin_str_check(bin_str: str) -> bool:
    """Check if the input is a valid binary string"""
    return all(c in "01" for c in bin_str)


def hex_str_to_bin(hex_str: str, width: int) -> str:
    """Convert hex string to binary string"""
    bin_str = bin(int(hex_str, 16))[2:].zfill(width)
    bin_len = len(bin_str)
    return bin_str[bin_len - width :]


def extract_exponent(bin_str: str, fp_fmt: FPFormat) -> str:
    """Extract the exponent bits from the binary string"""
    msb_idx = fp_fmt.exponent[0]
    lsb_idx = fp_fmt.exponent[1] - 1
    assert fp_fmt.exponent[1] > 1, "Invalid Exponent Index"
    return bin_str[msb_idx:lsb_idx:-1]


def extract_mantissa(bin_str: str, fp_fmt: FPFormat) -> str:
    """Extract the mantissa bits from the binary string"""
    msb_idx = fp_fmt.mantissa[0]
    if fp_fmt.mantissa[1] == 0:
        return bin_str[msb_idx::-1]
    else:
        lsb_idx = fp_fmt.mantissa[1] - 1
        return bin_str[msb_idx:lsb_idx:-1]


def extract_sign(bin_str: str, fp_fmt: FPFormat) -> str:
    """Extract the sign bit from the binary string"""
    return bin_str[fp_fmt.width - 1]


def hex_extractor(hex_str: str, fp_fmt: FPFormat) -> Fp:
    """Extract the sign, exponent, and mantissa from the hex string"""
    if not hex_str_check(hex_str):
        raise ValueError(f"Invalid Hex Value: [{hex_str}]")

    # reverse the binary string to get the little-endian format
    bin_str = hex_str_to_bin(hex_str, fp_fmt.width)[::-1]
    assert len(bin_str) == fp_fmt.width, "Invalid binary string length"
    return Fp(
        extract_sign(bin_str, fp_fmt),
        extract_exponent(bin_str, fp_fmt),
        extract_mantissa(bin_str, fp_fmt),
    )


def bin_extractor(bin_str: str, fp_fmt: FPFormat) -> Fp:
    """Extract the sign, exponent, and mantissa from the binary string"""
    if not bin_str_check(bin_str):
        raise ValueError(f"Invalid Binary Value: [{bin_str}]")

    bin_str = bin_str.zfill(fp_fmt.width)
    bin_len = len(bin_str)
    # clip the binary string to the required width
    tmp_str = bin_str[bin_len - fp_fmt.width :]
    # reverse the binary string to get the little-endian format
    fp_str = tmp_str[::-1]
    assert len(fp_str) == fp_fmt.width, "Invalid binary string length"
    return Fp(
        extract_sign(fp_str, fp_fmt),
        extract_exponent(fp_str, fp_fmt),
        extract_mantissa(fp_str, fp_fmt),
    )


def bin_formatter(bin_str: str) -> str:
    """Format the binary string for better readability"""
    return "_".join(bin_str[i : i + 4] for i in range(0, len(bin_str), 4))


class FPExtractor:
    def __init__(self, fmt_name: str, fp_fmt: FPFormat):
        self.fmt_name = fmt_name
        self.fp_fmt = fp_fmt
        self.sign = None
        self.exponent = None
        self.mantissa = None

    def extract_fp_str(self, fp_str: str) -> None:
        """Extract the sign, exponent, and mantissa from the input string"""
        fp_str = fp_str.lower()
        if fp_str.startswith("0x"):
            self.extract_hex(fp_str[2:])
        elif fp_str.startswith("0b"):
            self.extract_bin(fp_str[2:])
        else:
            raise ValueError(f"Input must start with 0x or 0b: [{fp_str}]")

    def extract_hex(self, hex_str: str) -> None:
        extract_dict = hex_extractor(hex_str, self.fp_fmt)
        self.sign = extract_dict.sign
        self.exponent = extract_dict.exponent
        self.mantissa = extract_dict.mantissa

    def extract_bin(self, bin_str: str) -> None:
        extract_dict = bin_extractor(bin_str, self.fp_fmt)
        self.sign = extract_dict.sign
        self.exponent = extract_dict.exponent
        self.mantissa = extract_dict.mantissa

    def get_exponent_value(self) -> int:
        return int(self.exponent, 2)

    def get_mantissa_value(self) -> int:
        return int(self.mantissa, 2)

    def is_positive(self) -> bool:
        return self.sign == "0"

    def get_e4m3_expression(
        self, exponent_value: int, mantissa_value: int, sign: str
    ) -> str:
        """Get the expression for the FP8_E4M3 format"""

        if exponent_value == 8 and mantissa_value == 7:
            return "NaN"
        elif exponent_value == -7:
            if mantissa_value == 0:
                return "+Zero" if sign == "1" else "-Zero"
            else:
                return f"Subnormal: sign:{sign}, exponent:{exponent_value + 1}, mantissa: 0.{self.mantissa}"
        else:
            return f"Normal: sign:{sign}, exponent:{exponent_value}, mantissa: 1.{self.mantissa}"

    def get_fp_expression(self) -> str:
        exponent_width = self.fp_fmt.exponent[0] - self.fp_fmt.exponent[1] + 1
        exponent_bias: int = 2 ** (exponent_width - 1) - 1
        exponent_original = self.get_exponent_value()
        exponent_effective = exponent_original - exponent_bias
        mantissa_value = self.get_mantissa_value()

        # Special case for FP8_E4M3 format
        # according to OFP8 specification
        if self.fmt_name == "FP8_E4M3":
            return self.get_e4m3_expression(
                exponent_effective, mantissa_value, self.sign
            )

        if exponent_effective == exponent_bias + 1:
            if mantissa_value == 0:
                return "+Inf" if self.is_positive() else "-Inf"
            else:
                return "NaN"
        elif exponent_original == 0:
            if mantissa_value == 0:
                return "+Zero" if self.is_positive() else "-Zero"
            else:
                return f"Subnormal: sign:{self.sign}, exponent:{exponent_effective + 1}, mantissa: 0.{self.mantissa}"
        else:
            return f"Normal: sign:{self.sign}, exponent:{exponent_effective}, mantissa: 1.{self.mantissa}"


class GUI(tk.Tk):
    def __init__(
        self,
        screenName=None,
        baseName=None,
        className="Tk",
        useTk=True,
        sync=False,
        use=None,
    ):
        super().__init__(screenName, baseName, className, useTk, sync, use)
        self.title("FP Extractor")
        self.geometry("1250x800")

        self.fp_extractors = {
            name: FPExtractor(name, fmt) for name, fmt in FP_CONFIG.items()
        }

        self.create_widgets()

    def create_widgets(self):
        canvas = tk.Canvas(self)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window(
            (0, 0), window=scrollable_frame, anchor="nw", width=self.winfo_width()
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 绑定鼠标滚轮事件
        canvas.bind_all(
            "<MouseWheel>", lambda event: self._on_mousewheel(event, canvas)
        )

        canvas.bind("<Configure>", lambda e: canvas.itemconfig("all", width=e.width))

        bold_font = font.Font(weight="bold")
        custom_font = font.Font(size=16)
        for name in self.fp_extractors:
            frame = tk.Frame(scrollable_frame, borderwidth=2, relief="groove")
            frame.pack(pady=20, fill="x", expand=True)

            label = tk.Label(frame, text=f"{name}", pady=4, font=bold_font)
            label.pack(side="top", padx=5)

            entry = tk.Entry(frame, width=50, fg="grey")
            default_text = "hex start with [0x], bin start with [0b]"
            entry.insert(0, default_text)
            # 绑定输入框获取焦点事件
            entry.bind(
                "<FocusIn>",
                lambda e, entry=entry, text=default_text: self.on_entry_click(
                    e, entry, text
                ),
            )
            # 绑定输入框失去焦点事件
            entry.bind(
                "<FocusOut>",
                lambda e, entry=entry, text=default_text, n=name: self.on_focusout(
                    e, entry, text, n
                ),
            )
            entry.pack(side="top", padx=5)
            # 绑定键盘释放事件
            entry.bind("<KeyRelease>", lambda e, n=name: self.update_bits(n))

            bits_frame = tk.Frame(frame)
            bits_frame.pack(side="top", padx=5, pady=5, fill="y", expand=True)
            # 保存bits_frame到fp_extractors
            self.fp_extractors[name].entry = entry

            result = tk.Label(frame, text="", font=custom_font)
            result.pack(pady=5)
            # 保存result_label到fp_extractors
            self.fp_extractors[name].result_label = result
            self.create_bit_labels(name, bits_frame)

    def _on_mousewheel(self, event, canvas):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_entry_click(self, event, entry, default_text):
        if entry.get() == default_text:
            entry.delete(0, "end")
            entry.insert(0, "")
            entry.config(fg="black")

    def on_focusout(self, event, entry, default_text, name):
        if entry.get() == "":
            entry.insert(0, default_text)
            entry.config(fg="grey")
            tmp_str = "0".zfill(self.fp_extractors[name].fp_fmt.width)
            self.update_bit_labels(name, tmp_str)

    def update_bits(self, fmt_name):
        extractor = self.fp_extractors[fmt_name]
        input_str: str = extractor.entry.get()
        fp_str = input_str.strip().replace("_", "").lower()
        if len(fp_str) > 2 and (fp_str.startswith("0x") or fp_str.startswith("0b")):
            try:
                extractor.extract_fp_str(fp_str)
                if fp_str.startswith("0x"):
                    bin_str = hex_str_to_bin(fp_str[2:], extractor.fp_fmt.width)
                else:
                    bin_str = fp_str[2:].zfill(extractor.fp_fmt.width)
                    bin_str = bin_str[len(bin_str) - extractor.fp_fmt.width :]
                self.update_bit_labels(fmt_name, bin_str)
                result_text = extractor.get_fp_expression()
            except ValueError as e:
                result_text = str(e)
            extractor.result_label.config(text=result_text)
        else:
            extractor.result_label.config(text="Please start with [0x] or [0b]")

    def create_bit_labels(self, fmt_name, frame):
        fp_fmt = self.fp_extractors[fmt_name].fp_fmt
        width = fp_fmt.width

        frame.columnconfigure((0, 1, 2), weight=1)
        frame.rowconfigure(0, weight=1)

        sign_frame = tk.Frame(frame)
        sign_frame.pack(side="left", fill="y", padx=5)

        exponent_frame = tk.Frame(frame)
        exponent_frame.pack(side="left", fill="y", padx=5)

        mantissa_frame = tk.Frame(frame)
        mantissa_frame.pack(side="left", fill="y", padx=5)

        self.fp_extractors[fmt_name].bit_labels = []

        for i in range(width):
            parent_frame = (
                sign_frame
                if i == 0
                else exponent_frame
                if i < width - fp_fmt.exponent[1]
                else mantissa_frame
            )
            if i == 0:
                parent_frame = sign_frame
                bg = "#00FA9A"
            elif i < width - fp_fmt.exponent[1]:
                parent_frame = exponent_frame
                bg = "yellow"
            else:
                parent_frame = mantissa_frame
                bg = "#FFA500"

            pos_frame = tk.Frame(parent_frame)
            pos_frame.pack(side="left", fill="y")
            bit_position_label = tk.Label(
                pos_frame,
                text=str(width - i - 1),
                borderwidth=1,
                width=2,
            )
            bit_label = tk.Label(
                pos_frame,
                text="0",
                borderwidth=1,
                relief="solid",
                width=2,
                bg=bg,
            )
            bit_position_label.pack(side="top", expand=True)
            bit_label.pack(side="top", expand=True)
            self.fp_extractors[fmt_name].bit_labels.append(bit_label)

    def update_bit_labels(self, fmt_name, bin_str):
        bit_labels = self.fp_extractors[fmt_name].bit_labels
        for i, bit_label in enumerate(bit_labels):
            bit_label.config(text=bin_str[i])


if __name__ == "__main__":
    app = GUI()
    app.mainloop()

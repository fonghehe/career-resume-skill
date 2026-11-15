# 导出中英文简历：Word 与 PDF

先准备已经核对的简历正文。导出只转换文件，不翻译、不修改事实，也不生成依据报告。还没有正文时先按[生成简历](generate-resume.md)让智能体从履历写作。

## 直接告诉智能体

```text
请把【实际版本目录】中的中英文简历分别导出为 Word 和 PDF。
中文保留单栏主题版式，英文使用黑白国际版式。
PDF 从各自的 DOCX 转换，保留 Markdown、依据报告和旧版本。
检查文本顺序、日期、字体和分页，说明实际完成了哪些检查。
```

无需先运行文档站。DOCX 只需要 Python 3.9+ 标准库；自动生成 PDF 还需本机 LibreOffice。没有它时可以先生成 DOCX，再用 Word 的「另存为 PDF」。工具不调用在线转换服务。

## 命令行导出

在自己的完整工作副本根目录运行，将示例路径换为实际正文：

```sh
# 中文 Word，A4；只用 Python
python3 scripts/career.py export "local/output/resumes/版本目录/resume.zh-CN.md"

# 英文 Word：文件名 resume.en.md 自动选择黑白国际版式和 US Letter
python3 scripts/career.py export "local/output/resumes/版本目录/resume.en.md"

# 同时生成同名 Word 与 PDF；需要本机 LibreOffice
python3 scripts/career.py export "local/output/resumes/版本目录/resume.zh-CN.md" --format all
python3 scripts/career.py export "local/output/resumes/版本目录/resume.en.md" --format all --page a4
```

`--format` 默认 `docx`，可选 `pdf` 或 `all`。从 Markdown 单独导出 `pdf` 时，DOCX 在临时目录构建，转换结束后清理；`all` 会保留两份文件。中英文复用相同的 DOCX 生成与 PDF 转换流程。

已有 Word 成稿应直接转换它，保留其实际排版：

```sh
python3 scripts/career.py export "local/output/resumes/版本目录/resume.en.docx" --format pdf
```

同名文件一律保留。已有 DOCX、尚无 PDF 时用上面的转换命令；需要重新导出两种格式时选择新版本目录，或给 `--output 新名称.pdf`。`all` 的 `--output` 必须是 `.pdf` 路径，DOCX 使用同一文件名。

## 切换工作副本、版式或转换器

```sh
python3 scripts/career.py --workspace /实际路径/my-career export "local/output/resumes/版本目录/resume.en.md"
python3 scripts/career.py export "英文正文.md" --layout international --page a4
python3 scripts/career.py export "中文正文.md" --theme sage --output "新的中文简历.docx"
python3 scripts/career.py export "正文.md" --format all --converter /实际路径/soffice
python3 scripts/career.py export "正文.md" --format pdf --font-dir /实际中文字体目录
```

统一入口中相对正文和导出路径按 `--workspace` 解析；未指定时使用脚本所属副本，不取决于终端当前目录。`init --new` 的新副本路径与当前终端目录有关，推荐使用绝对路径。

只有文件名以 `.en.md` 结尾时才自动判断为英文版式；其他文件名默认中文版式，可显式指定 `--layout international`。英文默认 Letter，A4 地区加 `--page a4`。国际版式忽略主题色。相对输入与输出路径按 `--workspace` 指定的完整副本解析，默认使用命令入口所属副本。

运行 `python3 scripts/career.py doctor` 可查看是否发现本地 PDF 转换器。没有转换器、转换失败或超时时会明确报错，不创建冒充成功的 PDF；`all` 转换失败时已生成且校验通过的 DOCX 会保留，错误信息给出其路径。不会自动安装软件。

## 在工作台下载

运行 `python3 scripts/career.py workbench`，进入「简历版本」，选择已保存的版本后下载 DOCX 或 PDF。当前草稿须先另存；下载针对选择的已保存版本。PDF 同样依赖本机 LibreOffice，英文版本自动使用国际版式，下载不会覆盖磁盘上的简历文件。

## 检查什么才算完成

导出器检查 DOCX 包完整性、正文顺序及常见日期问题；PDF 转换器检查退出状态与文件完整标记。这些检查不等于排版验收，也不能证明第三方 ATS 解析结果。

打开实际 DOCX / PDF，核对姓名、联系方式、长单位名称、日期对齐、中文缺字、页数、行距和跨页标题。PDF 必须逐页检查；缺少可用渲染工具时说明尚未完成视觉检查。来源译名、资格和数字继续以依据报告中的确认状态为准。

如果中文 PDF 出现方框字，先检查转换器能否加载中文字体。macOS 无界面转换会在该次进程中加入系统字体目录，不更改系统设置；其他环境可用重复的 `--font-dir /字体目录` 指定本机已有字体。字体目录和临时字体缓存只用于转换，工具不下载字体。即使 PDF 可以提取出正确文字，也必须查看实际页面是否缺字。

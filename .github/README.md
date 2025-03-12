# TinyLean

![Supported Python versions](https://img.shields.io/pypi/pyversions/TinyLean)
![Lines of Python](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/anqurvanillapy/5d8f9b1d4b414b7076cf84f4eae089d9/raw/cloc.json)
[![Test](https://github.com/anqurvanillapy/TinyLean/actions/workflows/test.yml/badge.svg)](https://github.com/anqurvanillapy/TinyLean/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/anqurvanillapy/TinyLean/graph/badge.svg?token=M0P3GXBQDK)](https://codecov.io/gh/anqurvanillapy/TinyLean)

仅用不到 1K 行 Python 实现的 Lean 4 风格定理证明器。

```lean
def TinyLean ≔ {T: Type} → (a: T) → T
```

* 你可以在这个项目中学到基础的**定理证明**（theorem proving）原理及其实现。
* 丰富的中文注释，并以**工业界常用词汇**的使用优先，帮助你轻松地将工业及学术用语联系在一起。
* 丰富的**单元测试**和高覆盖率，帮助你在做出任何修改时执行回归测试，或改写成其他语言项目时当做参考。

> [!NOTE]
> In pre-`v1` releases I used English everywhere in this project for convenience. So I feel very sorry for the early
> stargazers who might not expect **full Chinese content** here (including documentation and comments), since I decided
> to retarget the audience. Please reach me if you have trouble of any kind.

## ❓ 疑问

> *“这个定理证明有多‘强’？”*

如果你了解甚至十分熟悉 PLT（编程语言理论）的知识，这个项目实现了以下语言特性：

<details>
<summary>点击展开剧透</summary>
<ul>
<li>Dependently-typed lambda calculus</li>
<li>Holes/goals</li>
<li>Implicit arguments (no first-class polymorphism)</li>
<li>Inductive data type (à la pi-forall)</li>
<li>Dependent pattern matching (à la pi-forall)</li>
<li>Typeclass (no chained instances)</li>
</ul>
</details>

TinyLean 可能是你能找得到的以上特性结合一块的最短实现。在本文末尾的**探索**部分你还能找到更多资料。

> *“我对定理证明不感兴趣，所以它还能做什么？”*

当你有一个比 C++、Java、TypeScript、Rust、Haskell 强大的类型系统，它的实现不到 1K 行，还适合移植到其他的语言时，再仔细思考一下你想拿它做些什么事情。

我用这些知识实现了 [RowScript] 编程语言，一个支持行多态（row polymorphism）的 JavaScript 方言。

[RowScript]: https://github.com/rowscript/rowscript

> *“项目名为什么是 TinyLean？为什么项目名不是 mini-lean，μLean 之类的其他名字呢？”*

“TinyLean”是对 [TinyIdris] 项目的致敬，TinyIdris 是一个“极简” Idris 编程语言的实现。

[TinyIdris]: https://github.com/edwinb/SPLV20

> *“为什么使用中文？”*

即使使用英文，PLT 领域内就连最简单的术语都充满着歧义和晦涩。如果你对 PLT
里的各种术语仍未祛魅，去搞清楚 [dependent sum type] 和 [sum type] 的区别吧，这是每一个 PLer 学习过程中必吃的 💩。

我会用尽可能简单、常见的语言和术语，来帮助你祛魅的过程。

[dependent sum type]: https://ncatlab.org/nlab/show/dependent+sum

[sum type]: https://ncatlab.org/nlab/show/sum+type

## ⏬ 安装

### 尝试

如果只是想尝试玩玩本项目，可以从 PyPI 上安装完整的实现：

```bash
pip install TinyLean
```

用 `tinylean` 命令执行任意 `.lean` 文件：

```bash
tinylean example.lean
```

甚至可以执行一个 Markdown 文件，所有标记了 <code>```lean</code> 的代码块都会执行类型检查。

> [!IMPORTANT]
> 你正在阅读的 README 文件是个合法的 TinyLean 文件！

```bash
tinylean example.md
```

### 本地阅读源码

克隆本项目：

```bash
git clone https://github.com/anqurvanillapy/TinyLean
cd TinyLean/
```

本地测试任何你的 `.lean`/`.md` 文件，比如本文件：

```bash
python -m src.TinyLean .github/README.md
```

安装并使用 `pytest` 执行所有单元测试：

```bash
pip install pytest
pytest
```

## 🧙指南

那么，欢迎来到定理证明的世界！让我们一步步实现如何优雅的证明旷世难题 `1+1=2`。

### DTLC

一开始，这个世界仅有这些东西：

* *类型的类型*（type of type，也叫 universe），即 `Type`
* 引用，又叫变量名，形如 `x`
* 函数，形如 `λ x y ↦ y`
* 函数类型，形如 `(x: Type) → (y: Type) → Type`
* 调用，形如 `x y`

这个世界有个名字，叫 DTLC（dependently-typed lambda calculus）。

做一些简单的 lambda 演算，比如定义一个叫 `id` 的恒等函数（identity function），接受一个 `a` 并返回去：

```lean
def id (T: Type) (a: T): T := a

def Hello: Type := Type

example := id Type Hello
```

### ITP 与 ATP

定理证明器的功能往往都是*交互式的*（ITP，interactive theorem proving），这的意思是，当你不太清楚目前证明所需要的信息时，你可以询问证明器，例如：

```lean
def myLemma
  (a: Type)
  (b: (_: Type) -> Type)
  (c: b a)
  : Type
  := Type
/-   ^~~^ 尝试将这里的“Type”换成“_“ -/

def myTheorem := myLemma Type (id Type) Type
```

当你把 `:= Type` 替换成 `:= _` 时，你在代码中就留下了一个“洞（hole，又叫 goal）”，证明器会告诉你在 `_`
的位置要求填什么类型的值，并且上下文中都有哪些变量可以使用。证明器会输出类似这样的信息：

```plaintext
.github/README.md:?:?: unsolved placeholder:
  ?u.? : Type

context:
  (a: Type)
  (b: (_: Type) → Type)
  (c: (b a))
```

而所谓的*自动定理证明*（ATP，automatic theorem proving），则是根据上下文可用的变量，自动填入符合类型限制的值。

TinyLean 能实现部分 ATP 的功能，可以填补一些“显而易见”的洞。而如你所见，完整的 ATP 是一个十分适合 AI 接手的问题。

### 隐式参数

TinyLean 支持*隐式参数*（implicit argument）的特性，将我们的 `id` 函数改写，可以省去我们对 `T` 参数的传递，类型检查器能推导出来。

```lean
def id1 {T: Type} (a: T): T := a

example := id1 Hello
```

而实际上，隐式参数的原理就是由证明器帮忙插入 `_`，来看是否能由证明器根据上下文自动填补答案。以上的例子等同于在 `id` 的调用中留下
`_`：

```lean
example := id _ Hello
```

此外，如果你想显式地赋予 `id1` 中 `T` 的参数，不想由证明器填补，则使用以下语法：

```lean
example := id1 (T := Type) Hello
```

### 邱奇数

仅用 DTLC，我们仍旧能够表达自然数（natural number），比如运用[邱奇数]（Church numerals）的方式。

定义 `CN` 类型：

```lean
def CN: Type :=
    (T: Type) -> (S: (n: T) -> T) -> (Z: T) -> T
```

定义一个数字 `3`，它形如“零的后继的后继的后继”：

```lean
def _3: CN := fun T S Z => S (S (S Z))
```

定义加法和乘法：

```lean
def addCN (a: CN) (b: CN): CN :=
    fun T S Z => (a T S) (b T S Z)

def mulCN (a: CN) (b: CN): CN :=
    fun T S Z => (a T) (b T S) Z
```

做些简单演算：

```lean
def _6: CN := addCN _3 _3
def _9: CN := mulCN _3 _3
```

[邱奇数]: https://en.wikipedia.org/wiki/Church_encoding

### 相等

编写证明最重要的工具是*相等*（equality），仅有 `1+1` 而不能证明 `1+1=2` 是荒唐的。而仅使用
DTLC，我们依旧可以表达出等式，比如运用[Leibniz 等式]的方式。

定义 `LEq` 类型、`lRefl`（reflexivity，自反性）和 `lSym`（symmetry，对称性）:

```lean
def LEq {T: Type} (a: T) (b: T): Type :=
    (p: (v: T) -> Type) -> (pa: p a) -> p b

def lRefl {T: Type} (a: T): LEq a a :=
    fun p pa => pa

def lSym {T: Type} (a: T) (b: T) (p: LEq a b): LEq b a :=
    (p (fun b => LEq b a)) (lRefl a)
```

让我们证明刚刚的 `_9 = _3 + _6`：

```lean
example: LEq _9 (addCN _3 _6) := lRefl _9
```

[Leibniz 等式]: https://en.wikipedia.org/wiki/Equality_(mathematics)

### 归纳数据类型

我们可以用归纳数据类型（inductive data type）来定义一个新的类型，比如我们终于可以有一个更直观的自然数了：

```lean
inductive N where
| Z
| S (n: N)
open N
```

这个定义已经非常接近[Peano 公理]所定义的自然数：

1. 0（`Z`）是一个自然数（`N`）
2. 对于所有自然数 `n`，`n` 的后继（`S n`）也是一个自然数

其加法定义，运用递归（recursion）也更加自然：

```lean
def addN (n: N) (m: N): N :=
  match n with
  | Z => m
  | S pred => S (addN pred m)

example := addN (S Z) (S Z)
```

假设一个归纳数据类型没有任何构造器（constructor），则它就是一个空类型（bottom type，即 ⊥）：

```lean
inductive Bot where
open Bot
```

[爆炸原理]（ex falso）是指我们可以从矛盾中获取出任何事物，我们可以用 `nomatch` 写出这样的定理：

```lean
def exFalso (T: Type) (x: Bot): T := nomatch x
```

这里，我们凭空拿出来了一个 `T` 类型的值。

[Peano 公理]: https://en.wikipedia.org/wiki/Peano_axioms

[爆炸原理]: https://en.wikipedia.org/wiki/Principle_of_explosion

### 索引类型

归纳数据类型是可以携带参数（parameter）的，携带参数时我们称这样的类型为索引类型（indexed type），因为它“被某个值索引（indexed
by a value）”。这样的类型我们还可以称作“归纳集（inductive family）”。

比如在 C++ 中，我们可以用“[非类型模板参数]（non-type template parameter）”实现 `std::array<int, 3>` 的写法，此时 `3`
记录着数组的长度，它只是一个普通的数值。

同样的，我们可以定义一个能在类型上记录长度的 vector 类型：

```lean
inductive Vec (A: Type) (n: N) where
| Nil (n := Z)
| Cons {m: N} (a: A) (v: Vec A m) (n := S m)
open Vec
```

这里的 `(n := Z)` 意思是指，当我使用 `Nil` 构造一个空 vector 时，它的类型参数 `n` 会被填为 `Z`，代表其长度为 0。

几个长度不同的 vector 的例子：

```lean
def v0: Vec Type Z := Nil
def v1: Vec Type (S Z) := Cons N v0
def v2: Vec Type (S (S Z)) := Cons CN v1
```

[非类型模板参数]: https://en.cppreference.com/w/cpp/language/template_parameters#Non-type_template_parameter

### 依赖模式匹配

索引类型能帮助我们排除掉不可能出现的模式（pattern）。举个例子，当我们使用 `Nil` 构造一个空 vector，并尝试对它进行 `match`
匹配时，很明显我们不需要再去考虑 `Cons` 的情况。这样的特性称作“依赖模式匹配（dependent pattern matching）”。

```lean
example :=
  match v0 with
  | Nil => Z
```

假设我们补充上 `Cons` 的情况，证明器会报出如下错误：

```plaintext
.github/README.md:?:?: type mismatch:
want:
  (Vec Type N.Z)

got:
  (Vec ?m.? (N.S ?m.?))
```

所以一个空类型不一定是没有构造器的类型，也有可能是完全没办法构造出来的类型，例如：

```lean
inductive Weird (n: N) where
| MkWeird (n := Z)
open Weird

example (A: Type) (x: Weird (S Z)): A := nomatch x
```

此时 `Weird (S Z)` 也是一个空类型，因为我们完全没办法构造一个这样类型的值。

### 新的相等类型

通过索引类型的特性，我们可以定义出更好理解的相等类型了：

```lean
inductive Eq {T: Type} (a: T) (b: T) where
| Refl (a := b)
open Eq
```

用 `addN` 和 `Eq` 测试一下我们的 `1+1=2`：

```lean
example: Eq (addN (S Z) (S Z)) (S (S Z)) := Refl (T := N)
```

### 类

在目前我们介绍的类型系统世界中，所有类型都同属于 `Type` 之下，我们没有办法对类型进行二次“归类”，这个 `Type` 忽然就变成了“新的
`any`”。这样的坏处在于，我希望 `int` 类型的默认值是 `0`，希望 `string` 类型的默认值是 `""`，而我能通过一个函数
`default::<T>` 就能生成这个类型的默认值，这要怎么做到呢？

类型类（typeclass，又叫 trait）则能很好地解决这个问题：

```lean
class Default (T: Type) where
  default: T
open Default
```

有了 `Default` 这个类（class）后，我们就可以为不同的类型定义 `Default` 的实例（instance）。

### 实例

为 `N` 类型定义它的默认值 `Z`：

```lean
instance: Default N
where
  default := Z
```

> [!CAUTION]
> 注意这里 `where` 关键词需要写到新的一行，因为 Lean 4 语法的灵活性很大，为了保持 TinyLean 语法声明文件的简洁，很多语法歧义尚未处理。

我们写个 `(default N) = Z` 的证明：

```lean
example: Eq Z (default N) := Refl (T := N)
```

### 类参数

我们可以使用类参数（class parameter）来检查某个类型（type）是否符合类（class）的要求，例如：

```lean
def mustBeDefault (T: Type) [p: Default T] := Type
```

调用 `mustBeDefault` 时，我们要求参数 `T` 符合 `Default` 这一个类的限制。

```lean
example := mustBeDefault N
```

很明晰，`N` 类型符合这个限制。而当我们传入其他的类型，例如 `Bot` 时，证明器会告诉我们找不到对应的实例声明：

```plaintext
.github/README.md:?:?: no such instance for class '(Default Bot)'
```

### 操作符重载

有了类，操作符重载（operator overloading）也能够轻松实现。在 TinyLean 中，中缀操作符 `+`、`-`、`*`、`/` 会被简单地翻译成
`add`、`sub`、`mul`、`div` 的函数调用，所以我们要先定义好对应的类和类方法（class method）：

```lean
class Add {T: Type} where
  add: (a: T) -> (b: T) -> T
open Add
```

> [!NOTE]
> 注意到这个 `add` 的操作是*同构*（homogenous）的，也就是输入和输出的类型都一致，更好的定义则是*异构*（heterogeneous）的，即类似
> `T → U → V` 的定义，在此我们省略异构加法的讨论。

为 `N` 类型定义相应的实例：

```lean
instance: Add (T := N)
where
  add := addN
```

这样，我们就能在 `1+1=2` 的证明中使用中缀操作符了：

```lean
example
  : Eq (S (S Z)) ((S Z) + (S Z))
  := Refl (T := N)
```

## 🔍 探索

接下来，你可以继续探索以下的世界：

### 源码

从 [`tests/onboard.py`] 文件开始阅读项目源码。

[`tests/onboard.py`]: ../src/TinyLean/tests/onboard.py

### 未知

如果你觉得在“指南”阶段仍有许多困惑，甚至完全没法理解发生了什么，这是正常的。“指南”实际上更像是对 TinyLean
特性的展示，而不是一个正儿八经的定理证明教程，因为这样的优质教程其实是很多的，例如：

* [Theorem Proving in Lean 4](https://leanprover.github.io/theorem_proving_in_lean4/)
* [Programming Language Foundations in Agda](https://plfa.github.io/)

这些教程/书籍对我而言，并不是第一次读了就全部懂了，而是三至四年内反复地、片段式地不断重复阅读其中的某些片段才明白的。

而我得坦白，让我真正理解类型论的方式，是自己亲手实现一个又一个类型论。

### 跃迁

TODO

## 🫡 致谢

TODO

---

<sub>MIT License Copyright © Anqur</sub>

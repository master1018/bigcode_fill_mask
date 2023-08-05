# bigcode gennerate

## 代码主体部分

代码中主要部分是LLM_Code_Generate类。

在类中初步定义4个元素：

> - source_code
>   - 源码.c文件的路径
>
> - mutattion_code
>   - 变异.c文件的路径
>
> - model
>   - 由transformers导入的model数据
>
> - tokenizer 
>   - 由transformers导入的tokenizer数据



下面将对类中的比较关键函数进行介绍，其余函数有的较为简单，有的没有用到，就不进行解释。

### import_model

```python
'''
@param path
			接收hugging face网站上所下载的模型数据的路径
'''
```

该函数通过transformers的库函数进行模型的导入。

目前代码中采用的是gpu进行计算。

### Import_dataset

```python
'''
@param path_src
			源码文件的路径
@param path_mut
			包含<mask>标识符，需要大模型进行填充的变异代码的路径
'''
```

通过os的一些指令将路径内的所有文件读取到类的source_code和mutattion_code元素内。

注意，这两个元素都是字典dict，key为hash值表示的文件夹，value为文件夹内所有文件的绝对路径组成的列表。

例如有以下文件夹：

```shell
mutation_insert_range
├── 10023_9d4853418ab2f754c2b63e091c29c5529b8b86ca_0
│   ├── insert_range_checker_0a70e8ca.c
│   ├── insert_range_checker_1c179ec6.c
│   ├── insert_range_checker_243442c8.c
│   ├── insert_range_checker_36a67dce.c
│   ├── insert_range_checker_3fd633ba.c
│   ├── insert_range_checker_409f04bb.c
│   ├── insert_range_checker_4f65c950.c
│   ├── insert_range_checker_5de1f218.c
```

则mutation_code的值应为：

```python
mutation_code = {
  "10023_9d4853418ab2f754c2b63e091c29c5529b8b86ca_0":
  	[
      ../insert_range_checker_0a70e8ca.c, ../insert_range_checker_1c179ec6.c,
    	../insert_range_checker_243442c8.c, ../insert_range_checker_36a67dce.c,
    	../insert_range_checker_3fd633ba.c, ../insert_range_checker_409f04bb.c, 
    	../insert_range_checker_4f65c950.c, ../insert_range_checker_5de1f218.c
    ]
}
```

### Generate_response

```python
'''
	@param request
				向大模型发送的请求，在代码中是包含<mask>需要进行填充的代码段
'''
```

利用transformers内的管道pipeline来调用模型的fill-mask功能。

注：在pipeline内，`device=0`表示模型进行计算时，用到gpu到0号卡上，如果gpu有1号卡可以用，则可以写成`device=1`。

### read_msg_list_from_file

该部分和按行读取文件的功能一样，只不过在读取的时候进行了过滤，将空行和注释进行过滤，不进行读入。

### get_statement_type

```python
'''
	@param code_line
				带有<mask>标识符的那一行代码
'''
```

该函数的功能在于识别当前代码行是什么语句，采用的方法比较简单粗暴，就是判断有误关键词"if"，"return"之类的。

### generate_input

```python
'''
	@param file_mut
				mutation_code内的路径中读取到的需要进行变异的代码文件
'''
```

函数中将<mask_ext>转换为<mask>，然后将所有的<mask>进行编号，为以下形式：

<mask0>, <mask1>, <mask2>, ..., <maskn>

### fill_mask_of_if_statement

对if语句内对<mask>进行填充。

通常if语句内原本的<maskn>会被扩展为"<mask><mask><mask><mask><mask><mask><mask><mask><mask><mask>"（可以对扩展的数量进行修改)

大模型对于每个<mask>都会产生5个得分由高到低的填充结果，如果按照深度搜索的思路，探索完所有路径，可以得到5^10种结果。但是实际中只需要3个结果即可，并且在生成第一轮结果后，将第一个<mask>替换为生成的结果，在重新对剩下的9个进行再次生成，会得到不一样的结果。

所以思路就是，对第一个<mask>，取得分最高的前三个结果，并替换标识符，假如先选取了其中的某一个，将其替换requet对应的<mask>后，重新用替换后的request发送给大模型，得到后面<mask>的结果，这时只选取第一个<mask>的填充结果，然后替换对应的<mask>得到新的request，再用request重复该过程，直到所有的<mask>都被替换后，此时便得到了request的一个最终输出。

例如：

```
<mask><mask> ... <mask> 
=> ref  假设第一步先去得分最高的输出ref
ref<mask><mask> ... <mask>  将ref替换对应的<mask>
=> fer  得到下一个<mask>的输出
reffer<mask> ... <mask>
=> _
reffer_<mask><mask> ... <mask>
=> val
reffer_val  最终的结果
```

### fill_mask_of_return_statement 

由于return语句过于简单，<mask>不用进行扩展，直接进行输出即可

### fill_mask_of_throw_statement

由于throw语句过于简单，<mask>不用进行扩展，直接进行输出即可

### llm_code_mutate

代码核心部分，主要负责生成请求，接收回应并进行代码的组装。

生成的代码将会在result_code下对应hash值的文件夹下。

#### win_size

函数中win_size参数控制请求窗口。由于模型的输入token有限制，并且生成的结果是与<mask>所在代码的上下文是有关的，因此win_size用于控制生成的请求取自于多少行代码，其中<mask>一定是位于中间行。

win_size的大小决定了请求中能够提供给<mask>的上下文信息的数量，目前的思路较为简单，只是简单的获取<mask>行的前、后各win_size/2行代码。

#### <mask>扩充

在前面已经说明扩充的目的，目前的代码设计的语句种类有if、return、throw，由于return和throw较为简单，所以不进行扩充，if语句目前初步定为扩充为10个<mask>。

扩充的数量决定了填充结果的详细程度，数量过少会导致填充不完善，甚至会出现一些无意义的结果。而数量过大，影响却较小，如果大模型实在不知道生成什么，它可能会使用一些条件表达式如（&&、｜｜）来进行重复的生成。但是数量过多的话也会影响性能以及输入的token数量。

#### 请求生成

前面已经说过窗口的设计，假设当前处理的是<mask1>，而在请求窗口中存在<mask0>，此时要做的就是将<mask0>替换为大模型生成的代码片段，而对于编号大于1（也就是还未被处理的<mask>，则不用理会）。

#### 代码生成

对于if，选择得分最高的前三个进行填充；对于return和throw，直接选取得分最高的那一个。



## FAQ

1、怎么运行？

直接python3 code_generate.py即可，考虑到运行的时间很长，可以使用以下命令挂在到后台：

```shell
nohup python3 code_generate.py &
```

注意：可以选择将输出定向到log文件，但要注意代码中有多少print输出，否则可能导致log文件过大，程序直接卡死。

2、怎么提升程序运行的效率？

目前通过nvidia-smi可以看到，程序在运行过程中，只使用了device 0，并且显存在2G左右。

因此要提升效率可以将代码改成多线程。或者复制code_generate.py为多份，规定哪一份代码用哪一个device去跑哪些代码文件的变异。

(比如可以修改i的范围，来规定当前进程处理的是哪些文件)

```python
for i in range(0, len(src_dirs)):
            if (src_dirs[i] == ".DS_Store"):
                continue # for mac os
            cur_dir_path = path_src + "/" + src_dirs[i] + "/"
            file_all = os.listdir(cur_dir_path)
            for j in range(0, len(file_all)):
                if ".c" == file_all[j][len(file_all[j]) - 2: len(file_all[j])]:
                    #code = self.read_msg_from_file(cur_dir_path + file_all[j])
                    self.source_code[src_dirs[i]] = cur_dir_path + file_all[j]
```

最后可能类似于这种运行：

```shell
nohup python3 code_generate1.py &
nohup python3 code_generate2.py &
nohup python3 code_generate3.py &
nohup python3 code_generate4.py &
...
```

但要注意对于文件的操作不要互斥，不能出现对于同一个文件同时写入，以及代码中可能有一些删除文件夹的操作，需要将其注释掉。

3、调整生成结果的质量的方式。

两种思路，一个是调整win_size以及<mask>上下文的获取逻辑，比如将函数名，一些重要的变量声明和语句加入到请求窗口中。

另一个是调整<mask>扩充到数量。

4、对于大模型的微调。

大模型的原仓库在hugging face 的codebert-c，里面有关于怎么训练和训练用的数据集。但我个人感觉意义不大，因为模型大小的限制，注定它不能像chatgpt一样效果显著，它更多的是依赖<mask>的上下文所提供的信息，另外对于特别抽象的代码，连人工都无法分辨怎么填充，可能大模型就直接hardcode了。

5、能够使用其他的大模型？

可以，但是要修改大模型处理请求的方式，有的大模型fill-mask的功能比较难用，估计不能直接用pipeline的方式来使用。而其目前在同等数量级的大模型中，codebert-c应该算是比较优越的了。

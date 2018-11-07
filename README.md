# HashFormat

Syntax dedicated to content with scripts to generate pages in any other format.

Hash Format is a custom syntax currently available only for the Kate editor, but will be made available to other editors (Vim is the next). So, you need to take the syntax file for your editor and place it in the right folder.

## Get started

I recommend you copy the `content` folder into your project (usually a book, but also a static website or other target text format). The `hashlib.py` file is needed to run `mymodel.model.py` files. Python must be present on your working environment to transform the `.hsh` files to the desired destination pages, just run the command: `python make.py`.

The user must know the hash syntax and how to build the models in python. Careful observation of the example files should provide all the necessary knowledge.

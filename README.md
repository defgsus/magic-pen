This is supposed to become a painting app utilizing all the trippy neural image generation techniques.
but i`m quite lacking time and GPU memory.

But here's a hack to run the stable-diffusion space on huggingface.co in a Qt application and
save all images to a `./results/` folder:

```shell
pip install -r requirements.txt

python src/app/generator
```

- `sub directory`: is the path below `./results/` and can be empty
- `filename slug`: is the beginning of the filename and will be appended with increasing numbers
- `prompt`, `negative prompt` and `guidance` do the usual thing

All jobs run in parallel ;-)
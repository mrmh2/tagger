import json
import time
import logging
from pathlib import Path

from pprint import pprint

import sys
from vispy import scene
from vispy import app
import numpy as np

from imageio import imread

import click

from dtoolcore import DataSet


canvas = scene.SceneCanvas(keys='interactive')
canvas.size = 600, 800
canvas.show()

view = canvas.central_widget.add_view()

tag_lookup = {
    '0': 'Untagged',
    '1': 'Brown rust',
    '2': 'Yellow rust',
    '3': 'Septoria',
    '4': 'Mildew',
    '5': 'Healthy'
}


def update():
    im = app.tis[app.n_current_image]
    app.image.set_data(im)
    position_text = f"[{1+app.n_current_image}/{len(app.tis)}]"
    current_tag = f"{app.tis.tags[app.n_current_image]}"
    if app.n_current_image > 0:
        prev_tag = app.tis.tags[app.n_current_image-1]
    else:
        prev_tag = "N/A"
    textstr = f"{position_text} - {current_tag} ({prev_tag})"
    app.t1.text = textstr
    canvas.update()


def dump_results():

    with open("results.csv", "w") as fh:

        fh.write("ImageNumber,Tag,Time\n")
        for n in range(len(app.tis)):
            
            try:
                tag_time = app.tis.tag_times[n] - app.tis.load_times[n]
            except KeyError:
                tag_time = -1

            fh.write(f"{n},{app.tis.tags[n]},{tag_time}\n")


@canvas.events.key_press.connect
def key_event(event):

    if event.key.name in tag_lookup:
        if 1 + app.n_current_image < len(app.tis):
            app.tis.tag_item(app.n_current_image, tag_lookup[event.key.name])
            app.n_current_image += 1
            update()

    if event.key.name == 'Left':
        if app.n_current_image > 0:
            app.n_current_image -= 1
        update()

    if event.key.name == 'S':
        dump_results()


class TaggableImageSet(object):

    def __init__(self, uri):
        self.dataset = DataSet.from_uri(uri)
        self.tags = {n: 'Untagged' for n in list(range(len(self.dataset.identifiers)))}
        self.load_times = {}
        self.tag_times = {}

    def __len__(self):
        return len(self.dataset.identifiers)

    def tag_item(self, index, tag):
        self.tags[index] = tag

        if index not in self.tag_times:
            self.tag_times[index] = time.time()

    def __getitem__(self, index):
        idn = list(self.dataset.identifiers)[index]
        image_fpath = self.dataset.item_content_abspath(idn)

        if index not in self.load_times:
            self.load_times[index] = time.time()

        return imread(image_fpath)


@click.command()
@click.argument("dataset_uri")
def main(dataset_uri):

    logging.basicConfig(level=logging.INFO)

    app.tis = TaggableImageSet(dataset_uri)
    logging.info(f"Loaded image set with {len(app.tis)} items")

    app.image = scene.visuals.Image(app.tis[0], parent=view.scene)
    app.n_current_image = 0

    textstr = "Status bar"
    t1 = scene.visuals.Text(textstr, parent=view.scene, color='red', pos=(300,-20))
    t1.font_size = 14
    app.t1 = t1

    view.camera = scene.PanZoomCamera(aspect=1)
    view.camera.set_range()
    view.camera.flip = (False, True, False)

    update()

    app.run()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os

from avral import avral
from avral.operation import AvralOperation, OperationException
from avral.io.types import *
from avral.io.responce import AvralResponce


class Layer2qgis(AvralOperation):
    def __init__(self):
        super(Layer2qgis, self).__init__(
            name="do_work",
            inputs=[
                ("webgis_addr", StringType()),
                ("id_map", StringType()),
                ("username", StringType()),
                ("password", StringType()),
            ],
            outputs=[
                ("output_file", FileType()),
            ],
        )

    def _do_work(self):
        webgis_addr = self.getInput("webgis_addr")
        id_map = self.getInput("id_map")
        username = self.getInput("username")
        password = self.getInput("password")

        if None in (webgis_addr, id_map):
            raise OperationException("Internal error: Wrong number of arguments")

        result_file = "result.zip"
        cmd = "python " + os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "do_work.py"
        )
        cmd = cmd + f" --webgis_addr {webgis_addr}" \
                    f" --id_map {id_map}" \
                    f" --username {username}" \
                    f" --password {password}"

        os.system(cmd)

        self.setOutput("result", result_file)

        return ()
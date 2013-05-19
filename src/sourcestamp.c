/* Copyright 2013 Daniel Narvaez
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <Python.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <dirent.h>
#include <string.h>
#include <sys/stat.h>

static PyObject *sourcestamp_compute(PyObject *self, PyObject *args);

static PyMethodDef module_methods[] = {
    {"compute", sourcestamp_compute, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initsourcestamp(void)
{
    Py_InitModule("sourcestamp", module_methods);
}

static void
list_dir(const char *dir, time_t *mtime, int *n_files)
{
    DIR *dp;
    struct dirent *entry;
    struct stat statbuf;
    char *current_dir;

    current_dir = get_current_dir_name();

    dp = opendir(dir);

    chdir(dir);

    while ((entry = readdir(dp)) != NULL) {
        *n_files = *n_files + 1;

        lstat(entry->d_name, &statbuf);

        if(S_ISDIR(statbuf.st_mode)) {
            if(strcmp(".", entry->d_name) == 0 ||
               strcmp("..", entry->d_name) == 0 ||
               strcmp(".git", entry->d_name) == 0)
                continue;

            list_dir(entry->d_name, mtime, n_files);
        }

        if (statbuf.st_mtime > *mtime) {
            *mtime = statbuf.st_mtime;
        }
    }

    chdir(current_dir);
    free(current_dir);

    closedir(dp);
}

static
PyObject *sourcestamp_compute(PyObject *self, PyObject *args)
{
    time_t mtime = 0;
    int n_files = 0;
    const char *path;
    char stamp[100];

    if (!PyArg_ParseTuple(args, "s", &path)) {
        return NULL;
    }

    list_dir(path, &mtime, &n_files);
    snprintf(stamp, 100, "%d - %lu", n_files, (long unsigned)mtime);

    return Py_BuildValue("s", stamp);
}

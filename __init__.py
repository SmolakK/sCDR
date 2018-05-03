# -*- coding: utf-8 -*-
def classFactory(iface):
	from cdr_gen import cdr_gen
	return cdr_gen(iface)
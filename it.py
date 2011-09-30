#! /usr/bin/env python
from __future__ import print_function

import csv
import argparse
from sys import argv
from collections import OrderedDict as ODict

class Test:
	def __init__(self, test_data):
		self.data = test_data
		self.fails = []

class Patient:
	def __init__(self, test_data):
		# First line of the file is patient name
		self.patient_name = test_data.readline().strip()

		td_f = csv.reader(test_data, dialect='excel-tab')
		tests = ODict()
		for test in td_f:
			# tests key = test name.
			#	value = test value.
			tests[test[0]] = Test(float(test[1]))
		self.tests = tests

	def __repr__(self):
		s = [ self.patient_name ]
		for test_name, test in self.tests.items():
			fails = test.fails
			if not fails:
				s.append('{0}\t{1}'.format(test_name, test.data))
			else:
				s.append('{0}\t{1}\t*'.format(test_name, test.data))
				for fail in fails:
					s.append('\t{0}'.format(fail))
		return '\n'.join(s)

	def check(self, rules):
		for rule in rules:
			rule.classify(self)

class RangeRule:
	def __init__(self, rd):
		# rd = rule_dict
		self.max  = float(rd['Max'])
		self.min  = float(rd['Min'])
		self.id   = int(rd['Id'])
		self.name = rd['Test']

	def get_test_name(self):
		return self.name

	def get_rule_id(self):
		return self.id

	def passes(self, patient_data):
		test_data = patient_data.tests[self.name].data
		if (self.min < test_data < self.max):
			return True
		return False

def cmp_func(cmp_str):
	fs = {
		'<' : lambda x, y: x < y,
		'<=': lambda x, y: x <= y,
		'>' : lambda x, y: x > y,
		'>=': lambda x, y: x >= y,
		'=' : lambda x, y: x == y
	}
	return fs[cmp_str]

class InteractionRule:
	def __init__(self, rd):
		self.id    = int(rd['Id'])
		self.test1 = rd['Test1']
		self.cmp1  = cmp_func(rd['Comparison1'])
		self.val1  = float(rd['Value1'])
		self.test2 = rd['Test2']
		self.cmp2  = cmp_func(rd['Comparison2'])
		self.val2  = float(rd['Value2'])

	def get_test_name(self):
		return self.test2

	def get_rule_id(self):
		return self.id

	def passes(self, patient_data):
		td1 = patient_data.tests[self.test1].data
		td2 = patient_data.tests[self.test2].data

		if (self.cmp1(td1, self.val1) and
			self.cmp2(td2, self.val2)):
			return False
		return True

class Rules:
	def __init__(self, fieldnames, mk_rule, name):
		self.rules = []
		self.mk_rule = mk_rule
		self.fieldnames = fieldnames
		self.name = name

	def add_rules(self, rule_file):
		lr = [] # local rules
		r_f = csv.DictReader(rule_file,
			dialect = 'excel-tab',
			fieldnames = self.fieldnames)

		for line in r_f:
			lr.append(self.mk_rule(line))
		self.rules += lr

	def add_rules_from_file(self, file_name):
		self.add_rules(open(file_name, 'r'))

	def classify(self, patient):
		for rule in self.rules:
			if not rule.passes(patient):
				# What test is causing the failure
				test_name = rule.get_test_name()
				# What rule is causing the failure
				rule_id = "{0} {1}".format(self.name,
						rule.get_rule_id())
				patient.tests[test_name].fails.append(rule_id)

class InteractionRules(Rules):
	def __init__(self, name):
		Rules.__init__(self,
			['Id', 'Test1', 'Comparison1', 'Value1',
				'Test2', 'Comparison2', 'Value2'],
			InteractionRule,
			name)

class RangeRules(Rules):
	def __init__(self, name):
		Rules.__init__(self,
			['Id', 'Test', 'Min', 'Max'],
			RangeRule, name)

def main(args):

	if (len(args) <> 4):
		print('usage: health <range rule file> <interaction rule file> <patient file>')
	rr_file = args[1]
	ir_file = args[2]
	patient_file = args[3]

	rr = RangeRules('Range')
	rr.add_rules_from_file(rr_file)

	ir = InteractionRules('Interaction')
	ir.add_rules_from_file(ir_file)

	p = Patient(open(patient_file, 'r'))

	p.check([rr, ir])

	print(p)

if (__name__ == "__main__"):
	main(argv)

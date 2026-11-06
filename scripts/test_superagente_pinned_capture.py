#!/usr/bin/env python3
"""Offline checks for fixed-destination HTTPS capture."""
import importlib.util
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("sc",Path(__file__).with_name("superagente_source_capture.py"))
sc=importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)
HOST="sede.agenciatributaria.gob.es"
ENTRY={"url":"https://"+HOST+"/Sede/procedimientos/GZ25.shtml","approved_host":HOST}
def resolver(*args,**kw):
    return [(None,None,None,None,("8.8.8.8",443))]
class Reply:
    status=200
    def getheader(self,name,default=""): return "text/html"
    def read(self,n): return b"<p>Official content sample</p>"
class Conn:
    def __init__(self,host,ip,timeout):
        self.host,self.ip=host,ip
        self.requests=[]
        self.closed=False
    def request(self,method,path,headers): self.requests.append((method,path,headers))
    def getresponse(self): return Reply()
    def close(self): self.closed=True
class Tests(unittest.TestCase):
    def test_ip_pinned_and_hostname_kept(self):
        result=sc.validated_target(ENTRY,resolver)
        self.assertEqual(result[1:3],(HOST,"8.8.8.8"))
    def test_single_resolution_and_no_reconnect_dns(self):
        called=[]
        def once(*a,**kw):
            called.append(a)
            return resolver(*a,**kw)
        conn=[]
        def make(*a,**kw):
            obj=Conn(*a,**kw)
            conn.append(obj)
            return obj
        out=sc.capture(ENTRY,resolver=once,connection_factory=make)
        self.assertEqual(len(called),1)
        self.assertEqual(out["text"],"Official content sample")
        self.assertEqual(conn[0].requests[0][2]["Host"],HOST)
        self.assertTrue(conn[0].closed)
    def test_tls_hostname_validation_enabled(self):
        c=sc.PinnedHTTPSConnection(HOST,"8.8.8.8")
        self.assertTrue(c._context.check_hostname)
        self.assertEqual(c._context.verify_mode,sc.ssl.CERT_REQUIRED)
    def test_invalid_host_blocked(self):
        with self.assertRaises(ValueError):
            sc.validated_target({**ENTRY,"approved_host":"www.boe.es"},resolver)
    def test_no_port_override(self):
        with self.assertRaises(ValueError):
            sc.validated_target({**ENTRY,"url":"https://"+HOST+":8443/page"},resolver)
    def test_redirect_response_is_blocked(self):
        class Redirect(Reply):
            status=302
        class ConnRedirect(Conn):
            def getresponse(self): return Redirect()
        with self.assertRaisesRegex(ValueError,"unexpected_http_status"):
            sc.read_pinned(ENTRY,resolver,connection_factory=ConnRedirect)
    def test_private_dns_resolution_blocked(self):
        def private(*args,**kw):
            return [(None,None,None,None,("192.168.1.1",443))]
        with self.assertRaisesRegex(ValueError,"non_public_dns"):
            sc.validated_target(ENTRY,private)
    def test_mixed_resolution_blocked(self):
        def mixed(*args,**kw):
            return resolver(*args,**kw)+[(None,None,None,None,("192.168.1.1",443))]
        with self.assertRaisesRegex(ValueError,"non_public_dns"):
            sc.validated_target(ENTRY,mixed)
    def test_http_error_is_blocked(self):
        class Bad(Reply):
            status=503
        class ConnBad(Conn):
            def getresponse(self): return Bad()
        with self.assertRaisesRegex(ValueError,"unexpected_http_status"):
            sc.read_pinned(ENTRY,resolver,connection_factory=ConnBad)
    def test_capture_does_not_mark_verified(self):
        result=sc.capture(ENTRY,resolver=resolver,connection_factory=Conn)
        self.assertFalse(result["source_provenance_verified"])
if __name__=="__main__":
    unittest.main()

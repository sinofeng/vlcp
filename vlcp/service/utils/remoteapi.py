import json

from vlcp.config import defaultconfig

from vlcp.event import RoutineContainer

from vlcp.utils.webclient import WebClient, WebException

from vlcp.server.module import Module,callAPI, api

@defaultconfig
class RemoteCall(Module):
    _default_target_url_map = {}

    def __init__(self,server):
        super(RemoteCall,self).__init__(server)
        self.app_routine = RoutineContainer(self.scheduler)
        # there is no need to run this container main, so don't append it
        # self.routines.append(self.app_routine)
        self.wc = WebClient()
        self.createAPI(api(self.call,self.app_routine))

    def call(self,remote_module,method,timeout,params):
        self._logger.info("remote call remote_module %r",remote_module)
        self._logger.info("remote call method %r", method)
        self._logger.info("remote call kwargs %r", params)

        if remote_module and remote_module in self.target_url_map:
            endpoints = self.target_url_map[remote_module]
            params = json.dumps(params).encode("utf-8")
            for endpoint in endpoints:
                url = endpoint + "/" + remote_module + "/" + method

                try:
                    for m in self.wc.urlgetcontent(self.app_routine,url,params,b'POST',
                                                   {"Content-Type":"application/json"},timeout=timeout):
                        yield m
                except WebException as e:
                    # this endpoint connection error , try next url
                    self._logger.warning(" url (%r) post error %r , break ..",url,e)
                    break
                except Exception:
                    self._logger.warning(" url (%r) connection error , try next ..", url)
                    continue

        else:
            self._logger.warning(" target (%r) url not existed, ignore it ",remote_module)

        self.app_routine.retvalue = []


def remoteAPI(container,targetname,name,params={},timeout=60.0):
    args = {"remote_module":targetname,"method":name,"timeout":timeout,"params":params}
    for m in callAPI(container,"remotecall","call",params=args,timeout=timeout + 20):
        yield m
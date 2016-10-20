<?php
namespace app\index\controller;
use \think\Controller;
use \think\View;
use \think\Db;
class Index extends \think\Controller
{
	private $tables = array("rank"=>"wx_rank","category"=>"wx_category","gzh"=>"wx_gzh");
    public function index()
    {
    	$sql = "select * from ".$this->tables['category'];
    	$cat_list = Db::query($sql);  
    	$cat_id = 1;
    	$sql = "select rank,wx_id from ".$this->tables['rank']." where cat_id = ".$cat_id;  
    	$wx_list = Db::query($sql);

        // 查询微信号详细信息
        foreach ($wx_list as $key => $val) {
        	$wx_id = $val['wx_id'];
        	$sql = "select * from ".$this->tables['gzh']." where wx_id=?";        	
        	$res = Db::query($sql,[$wx_id]);   
        	if(count($res)){
        		$new_arr = array_merge($wx_list[$key],$res[0]); 
        		$wx_list[$key] = $new_arr;   
        	}           	
        }
        // 批量赋值
        $this->assign([
            'name'  => 'ThinkPHP',
            'cat_list' => $cat_list,
            'wx_list'=> $wx_list
        ]);
        // 模板输出
        return $this->fetch('index');
    }
}

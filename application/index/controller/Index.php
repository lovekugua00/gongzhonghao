<?php
namespace app\index\controller;
use \think\Controller;
use \think\View;
use \think\Db;
class Index extends \think\Controller
{
	private $tables = array("rank"=>"wx_rank","category"=>"wx_category");
    public function index()
    {
    	$sql = "select * from ".$this->tables['category'];
    	$result = Db::query($sql);
        // 模板变量赋值
        $this->assign('category',$result);
        $this->assign('email','thinkphp@qq.com');
        // 或者批量赋值
        $this->assign([
            'name'  => 'ThinkPHP',
            'email' => 'thinkphp@qq.com'
        ]);
        // 模板输出
        return $this->fetch('index');
    }
}

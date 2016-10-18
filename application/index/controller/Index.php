<?php
namespace app\index\controller;
use think\Db;
class Index
{
	private $tables = array("rank"=>"wx_rank");
    public function index()
    {
    	$result = Db::query("select * from ".$this->tables['rank']);
    	return json_encode($result);
    }
}

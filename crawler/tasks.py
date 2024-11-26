from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from .views import MistTrackScraper

channel_layer = get_channel_layer()

@shared_task(bind=True)
def crawl_address(self, address, group_name):
    """
    爬取单个地址的任务
    """
    try:
        # 更新进度
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'task_progress',
                'message': {
                    'status': 'processing',
                    'progress': 0,
                    'address': address,
                }
            }
        )

        # 执行爬取
        scraper = MistTrackScraper()
        result = scraper.search_address(address)

        # 发送结果
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'task_progress',
                'message': {
                    'status': 'completed',
                    'progress': 100,
                    'address': address,
                    'result': result
                }
            }
        )

        return {'status': 'success', 'result': result}

    except Exception as e:
        # 发送错误信息
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'task_progress',
                'message': {
                    'status': 'error',
                    'progress': 100,
                    'address': address,
                    'error': str(e)
                }
            }
        )
        return {'status': 'error', 'error': str(e)}

@shared_task(bind=True)
def crawl_batch(self, addresses, group_name):
    """
    批量爬取地址的任务
    """
    total = len(addresses)
    results = []

    for i, address in enumerate(addresses):
        try:
            # 更新进度
            progress = int((i / total) * 100)
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'task_progress',
                    'message': {
                        'status': 'processing',
                        'progress': progress,
                        'current': i + 1,
                        'total': total,
                        'address': address,
                    }
                }
            )

            # 执行爬取
            scraper = MistTrackScraper()
            result = scraper.search_address(address)
            results.append({
                'address': address,
                'status': 'success',
                'result': result
            })

        except Exception as e:
            results.append({
                'address': address,
                'status': 'error',
                'error': str(e)
            })

    # 发送完成信息
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'task_progress',
            'message': {
                'status': 'completed',
                'progress': 100,
                'results': results
            }
        }
    )

    return {'status': 'success', 'results': results}

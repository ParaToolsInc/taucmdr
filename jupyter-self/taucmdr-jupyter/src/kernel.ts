import { KernelModel } from './model';
import { IOutput,
         IStream } from '@jupyterlab/nbformat';

export async function updateTable(kernel: KernelModel, body: HTMLElement) {
  var kernel_output = await kernelMessage(kernel);
  var para = document.createElement('p');
  para.innerText = kernel_output.text as string;
  body.appendChild(para);
}

async function kernelMessage(kernel: KernelModel) {
  //kernel.execute('import kernel\nkernel.run()');
  await kernel.execute('10 + 10')
  var output = await kernel.output as IOutput;
  return output.data as IStream;
}
